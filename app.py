import tkinter as tk
from tkinter import filedialog, Text
import os
from PIL import ImageTk, Image
import registration
import SimpleITK as sitk

def run_app():
    imgs = ["None", "None"]

    root = tk.Tk()

    def add_fixed():
        file_name = filedialog.askopenfilename(initialdir='/home/piotr/Downloads/md/data', title="Select Image")
        imgs[0] = file_name
        label = tk.Label(fixed_frame, text='Label is set')
        label.pack()

    def add_moving():
        imgs[1] = filedialog.askopenfilename(initialdir='/home/piotr/Downloads/md/data', title="Select Image")
        label = tk.Label(moving_frame, text='Label is set')
        label.pack()


    def run_registration():
        image = ImageTk.PhotoImage(Image.open("/home/piotr/Downloads/md/data/iteration000.jpg"))
        label = tk.Label(result_frame, image=image)
        label.pack()
        registration.register(imgs[0], imgs[1], label)



    canvas = tk.Canvas(root, height=700, width=700, bg="#263D42")
    canvas.pack()

    # Fixed frame
    fixed_frame = tk.Frame(root, bg="white")
    fixed_frame.place(relwidth=0.5, relheight=0.5)

    # Moving frame
    moving_frame = tk.Frame(root, bg="white")
    moving_frame.place(relwidth=0.5, relheight=0.5, relx=0.5, rely=0)

    result_frame = tk.Frame(root, bg='black')
    result_frame.place(relheight=0.375, relwidth=0.5, relx=0.25, rely=0.5)

    choose_fixed_image_button = tk.Button(root, text="Fixed image", padx=10, pady=5, fg="white",
                                          bg="#263D42", command=add_fixed)

    choose_moving_image_button = tk.Button(root, text="Moving image", padx=10, pady=5, fg="white",
                                           bg="#263D42", command=add_moving)

    choose_fixed_image_button.pack()
    choose_moving_image_button.pack()


    run_button = tk.Button(root, text="Run simple registration", padx=10, pady=5, fg="white",
                                           bg="#263D42", command=run_registration)

    run_button.pack()

    root.mainloop()


if __name__ == "__main__":
    run_app()
