import SimpleITK as sitk

import numpy as np
import nibabel as ni


def run_app():
    mri_image_1 = sitk.ReadImage("first.nii")
    read_result_1 = sitk.ReadTransform('ct2mrT1.tfm')

    result_1 = mri_image_1 * read_result_1

    sitk.WriteImage(result_1, "first_q.nii")

    mri_image_2 = sitk.ReadImage("second.nii")
    read_result_2 = sitk.ReadTransform('ct2mrT2.tfm')

    result_2 = mri_image_2 * read_result_2

    sitk.WriteImage(result_2, "second_q.nii")


def merge_nii_files(sfile, ns):
    # This will load the first image for header information
    img = ni.load(sfile % (3, ns[0]))
    dshape = list(img.shape)
    dshape.append(len(ns))
    data = np.empty(dshape, dtype=img.get_data_dtype())

    header = img.header
    equal_header_test = True

    # Now load all the rest of the images
    for n, i in enumerate(ns):
        img = ni.load(sfile % (3, i))
        equal_header_test = equal_header_test and img.header == header
        data[..., n] = np.array(img.dataobj)

    imgs = ni.Nifti1Image(data, img.affine, header=header)
    if not equal_header_test:
        print("WARNING: Not all headers were equal!")
    return (imgs)


if __name__ == "__main__":
    nii_files = "example_%0*d.nii"
    images = merge_nii_files(nii_files, range(1, 2))
    ni.save(images, 'joined_image.nii')