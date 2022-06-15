import os
import SimpleITK as sitk
import tk
from PIL import ImageTk, Image
from threading import Thread

def save_combined_central_slice(fixed, moving, transform, file_name_prefix, moving_image, registration_method, gui):
    global iteration_number
    central_indexes = [int(i / 2) for i in fixed.GetSize()]

    moving_transformed = sitk.Resample(moving, fixed, transform,
                                       sitk.sitkLinear, 0.0,
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


def register(fixed_image_name, moving_image_name, gui):
    # read the images
    fixed_image = sitk.ReadImage(fixed_image_name, sitk.sitkFloat32)
    moving_image = sitk.ReadImage(moving_image_name, sitk.sitkFloat32)

    transform = sitk.CenteredTransformInitializer(fixed_image,
                                                  moving_image,
                                                  sitk.Euler3DTransform(),
                                                  sitk.CenteredTransformInitializerFilter.MOMENTS)

    # multi-resolution rigid registration using Mutual Information
    registration_method = sitk.ImageRegistrationMethod()
    registration_method.SetMetricAsMattesMutualInformation()
    registration_method.SetMetricSamplingStrategy(registration_method.REGULAR)
    registration_method.SetMetricSamplingPercentage(0.01)
    registration_method.SetInterpolator(sitk.sitkBSplineResampler)
    # registration_method.SetOptimizerAsGradientDescent(learningRate=0.008,
    #                                               numberOfIterations=100,
    #                                               convergenceMinimumValue=1e-6,
    #                                               convergenceWindowSize=20)
    registration_method.SetOptimizerAsLBFGSB(
        numberOfIterations=100)
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

    new_thread = Thread(target=registration_method.Execute,
                        args=(fixed_image, moving_image))
    # final_transform = registration_method.Execute(fixed_image, moving_image)
    final_transform = new_thread.start()
    # new_thread.join()

    # print('Optimizer\'s stopping condition, {0}'.format(registration_method.GetOptimizerStopConditionDescription()))
    # print("Metric value after  registration: ", registration_method.GetMetricValue())

    # sitk.WriteTransform(final_transform, 'output/ct2mrT1.tfm')
