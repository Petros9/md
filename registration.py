import os
import SimpleITK as sitk
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



def save_combined_central_slice(fixed, moving, transform, file_name_prefix, moving_image, registration_method, gui):
    global iteration_number
    central_indexes = [int(i / 2) for i in fixed.GetSize()]

    moving_transformed = sitk.Resample(moving, fixed, transform,
                                       sitk.sitkLinear, 0.0, # czy tu ma byc ta sama interpolacja co w registration() ??????
                                       moving_image.GetPixelIDValue())
    # extract the central slice in xy, xz, yz and alpha blend them
    combined = [fixed[:, :, central_indexes[2]] + -
    moving_transformed[:, :, central_indexes[2]],
                fixed[:, central_indexes[1], :] + -
                moving_transformed[:, central_indexes[1], :],
                fixed[central_indexes[0], :, :] + -
                moving_transformed[central_indexes[0], :, :]]

    # resample the alpha blended images to be isotropic and rescale intensity
    # values so that they are in [0,255], this satisfies the requirements
    # of the jpg format
    print(iteration_number, ": ", registration_method.GetMetricValue())
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
    # image = ImageTk.PhotoImage(Image.open(os.path.abspath(os.getcwd())+"\\output\\iteration{0}.jpg".format(next_image_number)))
    # label.configure(image=image)
    gui.update_result_image(next_image_number)
    iteration_number += 1


# function which runs whole registration in thread (gui was freezing)
def register(fixed_image_name, moving_image_name, gui, interpolation_method, sampling_percent, 
            sampling_strategy, bins, optimalizer, opt_data): 
    print(float(sampling_percent))

    new_thread = Thread(target=registration_computation, daemon=True,
                        args=(fixed_image_name, moving_image_name, gui, interpolation_method,sampling_percent,
                        sampling_strategy, bins, optimalizer, opt_data))
    final_transform = new_thread.start()
   


def registration_computation(fixed_image_name, moving_image_name, gui, interpolation_method, 
                            sampling_percent, sampling_strategy, bins, optimalizer, opt_data):
      # read the images
    fixed_image = sitk.ReadImage(fixed_image_name, sitk.sitkFloat32)
    moving_image = sitk.ReadImage(moving_image_name, sitk.sitkFloat32)

    transform = sitk.CenteredTransformInitializer(fixed_image,
                                                  moving_image,
                                                  sitk.Euler3DTransform(),
                                                  sitk.CenteredTransformInitializerFilter.MOMENTS)

    # multi-resolution rigid registration using Mutual Information
    registration_method = sitk.ImageRegistrationMethod()
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

    registration_method.SetInitialTransform(transform)

    # add iteration callback, save central slice in xy, xz, yz planes
    global iteration_number
    iteration_number = 0
    registration_method.AddCommand(sitk.sitkIterationEvent,
                                   lambda: save_combined_central_slice(fixed_image,
                                                                       moving_image,
                                                                       transform,
                                                                       'output/iteration', moving_image,
                                                                       registration_method, gui))
    
    print("Initial metric: ", registration_method.MetricEvaluate(fixed_image, moving_image))
    final_transform = registration_method.Execute(fixed_image, moving_image)

    print('Optimizer\'s stopping condition, {0}'.format(registration_method.GetOptimizerStopConditionDescription()))
    gui.set_results_text('Optimizer\'s stopping condition, {0}'.format(registration_method.GetOptimizerStopConditionDescription()))
    # print("Metric value after  registration: ", registration_method.GetMetricValue())

    # sitk.WriteTransform(final_transform, 'output/ct2mrT1.tfm')


