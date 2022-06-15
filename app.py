import os
import tkinter as tk
from tkinter import filedialog, Text
import registration
from PIL import ImageTk, Image
import SimpleITK as sitk
import matplotlib.pylab as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

FIX_IDX = 0

MOV_IDX = 0


def run_app():
    images = ["None", "None"]

    root = tk.Tk()


    def create_working_img(file_name, frame):
        itk_image = sitk.ReadImage(file_name, sitk.sitkFloat32)
        image_array = sitk.GetArrayViewFromImage(itk_image)

        def update_image(IDX):
            for widget in frame.winfo_children():
                widget.destroy()

            itk_image = sitk.ReadImage(file_name, sitk.sitkFloat32)
            image_array = sitk.GetArrayViewFromImage(itk_image)
            fig = plt.figure(figsize=(5, 4))
            print(IDX)
            plt.imshow(image_array[int(IDX)], cmap='Greys_r')
            canvas_figure = FigureCanvasTkAgg(fig, master=frame)
            canvas_figure.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        update_image(0)


        scale = tk.Scale(root, from_=0, to=len(image_array) - 1, orient='horizontal',
                         command=update_image)
        scale.pack()

    def add_image(idx, frame):
        file_name = filedialog.askopenfilename(initialdir=os.path.abspath(os.getcwd())+"\\data", title="Select Image")
        images[idx] = file_name
        create_working_img(file_name, frame)

    def run_registration():
        image = ImageTk.PhotoImage(Image.open(os.path.abspath(os.getcwd())+"\\output/iteration000.jpg"))
        label = tk.Label(result_frame, image=image)
        label.pack()
        registration.register(images[0], images[1], label)

    canvas = tk.Canvas(root, height=700, width=700, bg="#263D42")
    canvas.pack()

    # Fixed frame
    fixed_frame = tk.Frame(root, bg="white")
    fixed_frame.place(relwidth=0.5, relheight=0.4)

    # Moving frame
    moving_frame = tk.Frame(root, bg="white")
    moving_frame.place(relwidth=0.5, relheight=0.4, relx=0.5, rely=0)

    result_frame = tk.Frame(root, bg='black')
    result_frame.place(relheight=0.375, relwidth=0.5, relx=0.25, rely=0.5)

    choose_fixed_image_button = tk.Button(root, text="Fixed image", padx=10, pady=5, fg="white",
                                          bg="#263D42", command=lambda: add_image(0, fixed_frame))

    choose_moving_image_button = tk.Button(root, text="Moving image", padx=10, pady=5, fg="white",
                                           bg="#263D42", command=lambda: add_image(1, moving_frame))

    choose_fixed_image_button.pack()
    choose_moving_image_button.pack()

    run_button = tk.Button(root, text="Run simple registration", padx=10, pady=5, fg="white",
                           bg="#263D42", command=run_registration)

    run_button.pack()

    root.mainloop()


if __name__ == "__main__":
    run_app()