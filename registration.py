from copy import copy
import os
from unittest import result
import SimpleITK as sitk
from matplotlib import pyplot as plt
import numpy as np
import tk
from PIL import ImageTk, Image
from threading import Thread



interpolation_options = [
    "sitkLinear",
    "sitkNearestNeighbor",
    "sitkBSpline",
    "sitkGaussian",
    "sitkHammingWindowedSinc",
    "sitkCosineWindowedSinc",
    "sitkWelchWindowedSinc",
    "sitkLanczosWindowedSinc",
    "sitkBlackmanWindowedSinc",
]

sampling_strategies = [
    "RANDOM",
    "REGULAR",
    "NONE"
]

optimizers = [
    "GradientDescent",
    "GradientDescentLineSearch",
    "RegularStepGradientDescent",
    "ConjugateGradientLineSearch",
    "LBFGSB"
]

deformable_regist = [
    'BSpline',
    'daemons'
]


def parse_interpolation(method):
    switch={
    "sitkLinear": sitk.sitkLinear,
    "sitkNearestNeighbor": sitk.sitkNearestNeighbor,
    "sitkBSpline": sitk.sitkBSpline,
    "sitkGaussian": sitk.sitkGaussian,
    "sitkHammingWindowedSinc":sitk.sitkHammingWindowedSinc,
    "sitkCosineWindowedSinc": sitk.sitkCosineWindowedSinc,
    "sitkWelchWindowedSinc": sitk.sitkWelchWindowedSinc,
    "sitkLanczosWindowedSinc": sitk.sitkLanczosWindowedSinc,
    "sitkBlackmanWindowedSinc": sitk.sitkBlackmanWindowedSinc,
      }

    return switch.get(method)

def parse_strategies(method, registration_method):
    switch={
    "RANDOM": registration_method.RANDOM,
    "REGULAR": registration_method.REGULAR,
    "NONE":registration_method.NONE
    }

    return switch.get(method)

 

def save_combined_central_slice(fixed, moving, transform, file_name_prefix, moving_image, registration_method, gui, opt_data):
    global iteration_number
    alpha = 0.1
    central_indexes = [int(i / 2) for i in fixed.GetSize()]

    moving_transformed = sitk.Resample(moving, fixed, transform,
                                       sitk.sitkLinear, 0.0, 
                                       moving_image.GetPixelIDValue())
    # extract the central slice in xy, xz, yz and alpha blend them
    # combined = [fixed[:, :, central_indexes[2]] + -
    # moving_transformed[:, :, central_indexes[2]],
    #             fixed[:, central_indexes[1], :] + -
    #             moving_transformed[:, central_indexes[1], :],
    #             fixed[central_indexes[0], :, :] + -
    #             moving_transformed[central_indexes[0], :, :]]

    combined = [(1.0 - alpha)*fixed[:,:,central_indexes[2]] + \
                   alpha*moving_transformed[:,:,central_indexes[2]],
                  (1.0 - alpha)*fixed[:,central_indexes[1],:] + \
                  alpha*moving_transformed[:,central_indexes[1],:],
                  (1.0 - alpha)*fixed[central_indexes[0],:,:] + \
                  alpha*moving_transformed[central_indexes[0],:,:]]
    
    # resample the alpha blended images to be isotropic and rescale intensity
    # values so that they are in [0,255], this satisfies the requirements
    # of the jpg format
    print(iteration_number, ": ", registration_method.GetMetricValue())
    results.append(registration_method.GetMetricValue())
    gui.set_metric(registration_method.GetMetricValue())
    combined_isotropic = []

    for img in combined:
        original_spacing = img.GetSpacing()
        original_size = img.GetSize()
        min_spacing = min(original_spacing)
        new_spacing = [min_spacing, min_spacing]
        new_size = [int(round(original_size[0] * (original_spacing[0] / min_spacing))),
                    int(round(original_size[1] * (original_spacing[1] / min_spacing)))]
        resampled_img = sitk.Resample(img, new_size, sitk.Transform(),
                                      sitk.sitkLinear, img.GetOrigin(),
                                      new_spacing, img.GetDirection(), 0.0,
                                      img.GetPixelIDValue())
        combined_isotropic.append(sitk.Cast(sitk.RescaleIntensity(resampled_img),
                                            sitk.sitkUInt8))

    # tile the three images into one large image and save using the given file
    # name prefix and the iteration number
    sitk.WriteImage(sitk.Tile(combined_isotropic, (1, 3)),
                    file_name_prefix + format(iteration_number, '03d') + '.jpg')
    next_image_number = format(iteration_number, '03d')
    
    gui.update_result_image(next_image_number)
    if iteration_number == 0 or iteration_number > int(getattr(opt_data, 'numberOfIterations').get()) - 2:
        gui.show_chess(fixed, moving_transformed)
    
    iteration_number += 1
    return moving_transformed
    

# function which runs whole registration in thread (gui was freezing)
def register(fixed_image_name, moving_image_name, gui, interpolation_method, sampling_percent, 
            sampling_strategy, bins, optimalizer, opt_data, transform_file, second_step='daemons'): 
    print(float(sampling_percent))
    global result_image 
    result_image = None

    new_thread = Thread(target=registration_computation, daemon=True,
                        args=(fixed_image_name, moving_image_name, gui, interpolation_method,sampling_percent,
                        sampling_strategy, bins, optimalizer, opt_data, transform_file, second_step))
    final_transform = new_thread.start()

    # print(results)
    # return 
   


def registration_computation(fixed_image_name, moving_image_name, gui, interpolation_method, 
                            sampling_percent, sampling_strategy, bins, optimalizer, opt_data, transform_file, second_step='BSpline'):
      
    global results
    results = []

      # read the images
    fixed_image = sitk.ReadImage(fixed_image_name, sitk.sitkFloat32)
    moving_image = sitk.ReadImage(moving_image_name, sitk.sitkFloat32)
    moving_2 = copy(moving_image)

    transform = sitk.CenteredTransformInitializer(fixed_image,
                                                  moving_image,
                                                  sitk.Euler3DTransform(),
                                                  sitk.CenteredTransformInitializerFilter.GEOMETRY)

    grid_physical_spacing = [50.0, 50.0, 50.0]  # A control point every 50mm
    image_physical_size = [
        size * spacing
        for size, spacing in zip(fixed_image.GetSize(), fixed_image.GetSpacing())
    ]
    mesh_size = [
        int(image_size / grid_spacing + 0.5)
        for image_size, grid_spacing in zip(image_physical_size, grid_physical_spacing)
    ]

    ffd_transform = sitk.BSplineTransformInitializer(
        image1=fixed_image, transformDomainMeshSize=mesh_size, order=3
    )



    #  rigid registration using Mutual Information
    registration_method = sitk.ImageRegistrationMethod()
    # registration_method.SetMetricAsMeanSquares()
    registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=bins)
    registration_method.SetMetricSamplingStrategy(parse_strategies(sampling_strategy, registration_method))
    registration_method.SetMetricSamplingPercentage(float(sampling_percent))
    registration_method.SetInterpolator(parse_interpolation(interpolation_method))

    if optimalizer == 'GradientDescent':
        registration_method.SetOptimizerAsGradientDescent(learningRate=float(getattr(opt_data, 'learningRate').get()),
                                                    numberOfIterations=int(getattr(opt_data, 'numberOfIterations').get()),
                                                    convergenceMinimumValue=float(getattr(opt_data, 'convergenceMinimumValue').get()),
                                                    convergenceWindowSize=int(getattr(opt_data, 'convergenceWindowSize').get()))
    elif optimalizer =='GradientDescentLineSearch':
        registration_method.SetOptimizerAsGradientDescentLineSearch(learningRate=float(getattr(opt_data, 'learningRate').get()),
                                                    numberOfIterations=int(getattr(opt_data, 'numberOfIterations').get()),
                                                    convergenceMinimumValue=float(getattr(opt_data, 'convergenceMinimumValue').get()),
                                                    convergenceWindowSize=int(getattr(opt_data, 'convergenceWindowSize').get()))
    elif optimalizer =='ConjugateGradientLineSearch':
        registration_method.SetOptimizerAsConjugateGradientLineSearch(learningRate=float(getattr(opt_data, 'learningRate').get()),
                                                    numberOfIterations=int(getattr(opt_data, 'numberOfIterations').get()),
                                                    convergenceMinimumValue=float(getattr(opt_data, 'convergenceMinimumValue').get()),
                                                    convergenceWindowSize=int(getattr(opt_data, 'convergenceWindowSize').get()))
    elif optimalizer =='RegularStepGradientDescent':
        registration_method.SetOptimizerAsRegularStepGradientDescent(learningRate=float(getattr(opt_data, 'learningRate').get()),
                                                    numberOfIterations=int(getattr(opt_data, 'numberOfIterations').get()),
                                                    minStep=float(getattr(opt_data, 'minStep').get())
                                                    )
    elif optimalizer == "LBFGSB":
        registration_method.SetOptimizerAsLBFGSB(
            numberOfIterations=int(getattr(opt_data, 'numberOfIterations').get()),
            gradientConvergenceTolerance = float(getattr(opt_data, 'gradientConvergenceTolerance').get()))

    registration_method.SetOptimizerScalesFromPhysicalShift()

    # transform = initial_transform
    registration_method.SetInitialTransform(transform, inPlace=True)

    # add iteration callback, save central slice in xy, xz, yz planes
    global iteration_number
    iteration_number = 0
    registration_method.AddCommand(sitk.sitkIterationEvent,
                                   lambda: save_combined_central_slice(fixed_image,
                                                                       moving_image,
                                                                       transform,
                                                                       'output/iteration', moving_image,
                                                                       registration_method, gui, opt_data))
    
    print("Initial metric: ", registration_method.MetricEvaluate(fixed_image, moving_image))
    final_transform = registration_method.Execute(fixed_image, moving_image)
    new_moving = save_combined_central_slice(fixed_image, moving_image,final_transform,'output/iteration', moving_image,
                                     registration_method, gui, opt_data)
    x = [x for x in range(iteration_number)]
    y =  results
    
    #gui.show_results(x,y)
    #if moving_image == moving_2:
    #    print('TAKIE SAMEEEEE')
    #if new_moving == moving_2:
    #    print('aaaaaaaaaa')

    #   DEFORMABLE REGISTRATION ####################################################

    # multi-resolution
    # registration_method.SetShrinkFactorsPerLevel(shrinkFactors=[4, 2, 1])
    # registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[2, 1, 0])
    # registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

    # Determine the number of Bspline control points using the physical spacing we want for the control grid. 
    if second_step == 'BSpline':
        grid_physical_spacing = [50.0, 50.0, 50.0] # A control point every 50mm
        image_physical_size = [size*spacing for size,spacing in zip(fixed_image.GetSize(), fixed_image.GetSpacing())]
        mesh_size = [int(image_size/grid_spacing + 0.5) \
                    for image_size,grid_spacing in zip(image_physical_size,grid_physical_spacing)]

        transform = sitk.BSplineTransformInitializer(image1 = fixed_image, 
                                                transformDomainMeshSize = mesh_size, order=3)
        print(f"Initial Number of Parameters: {transform.GetNumberOfParameters()}")

        # R = sitk.ImageRegistrationMethod()
        # R.SetMetricAsMattesMutualInformation(50)
        
        # R.SetOptimizerAsGradientDescentLineSearch(
        #     5.0, 100, convergenceMinimumValue=1e-4, convergenceWindowSize=5
        # )

        # R.SetInterpolator(sitk.sitkLinear)

        registration_method.SetInitialTransformAsBSpline(transform, inPlace=True, scaleFactors=[1, 2, 5])
       

    elif second_step=='deamons':
        print('deamons')
        # registration_method = sitk.ImageRegistrationMethod()
        transform_to_displacment_field_filter = sitk.TransformToDisplacementFieldFilter()
        transform_to_displacment_field_filter.SetReferenceImage(fixed_image)
        transform = sitk.DisplacementFieldTransform(transform_to_displacment_field_filter.Execute(sitk.Transform()))

        # registration_method = sitk.FastSymmetricForcesDemonsRegistrationFilter()
        # registration_method.SetNumberOfIterations(int(getattr(opt_data, 'numberOfIterations').get()))
        # # Standard deviation for Gaussian smoothing of displacement field
        # registration_method.SetStandardDeviations(1.0)

        # initial_transform = sitk.DisplacementFieldTransform(final_transform)
        transform.SetSmoothingGaussianOnUpdate(
            varianceForUpdateField=0.0, varianceForTotalField=2.0)

        registration_method.SetInitialTransform(transform)
        registration_method.SetMetricAsDemons(10)

    elif second_step =='SMS':
        pass


    registration_method.SetShrinkFactorsPerLevel([4, 2, 1])
    registration_method.SetSmoothingSigmasPerLevel([2, 1, 0])
    registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
    registration_method.AddCommand(sitk.sitkIterationEvent,
                                   lambda: save_combined_central_slice(fixed_image,
                                                                       new_moving,
                                                                       transform,
                                                                       'output/iteration', moving_image,
                                                                       registration_method, gui, opt_data))
    
    print("Initial metric: ", registration_method.MetricEvaluate(fixed_image, new_moving))
    final_transform = registration_method.Execute(fixed_image, new_moving)

    # if second_step == 'deamons':
    #     final_transform = sitk.DisplacementFieldTransform(final_transform)

    save_combined_central_slice(fixed_image,moving_image,final_transform,'output/iteration', moving_image,
                                     registration_method, gui, opt_data)


    print('Optimizer\'s stopping condition, {0}'.format(registration_method.GetOptimizerStopConditionDescription()))
    # gui.set_results_text('Optimizer\'s stopping condition, {0}'.format(registration_method.GetOptimizerStopConditionDescription()))
    # print("Metric value after  registration: ", registration_method.GetMetricValue())

    sitk.WriteTransform(final_transform, transform_file+'.tfm') 
    x = [x for x in range(iteration_number)]
    y =  results

    
    gui.show_results(x,y)
    


