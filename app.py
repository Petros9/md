import tkinter as tk
from tkinter import filedialog, Text
import os



def run_app():
    imgs = ["None", "None"]

    root = tk.Tk()

    def add_image(idx, frame):
        file_name = filedialog.askopenfilename(initialdir='/home/piotr/Downloads/md/data', title="Select Image")
        print(file_name)
        imgs[idx] = file_name

        label = tk.Label(frame, text=imgs[idx])
        label.pack()


    canvas = tk.Canvas(root, height=700, width=700, bg="#263D42")
    canvas.pack()

    # Fixed frame
    fixed_frame = tk.Frame(root, bg="white")
    fixed_frame.place(relwidth=0.5, relheight=0.5)

    # Moving frame
    moving_frame = tk.Frame(root, bg="white")
    moving_frame.place(relwidth=0.5, relheight=0.5, relx=0.5, rely=0)

    choose_fixed_image_button = tk.Button(root, text="Fixed image", padx=10, pady=5, fg="white",
                                          bg="#263D42", command=add_image(0, fixed_frame))

    choose_moving_image_button = tk.Button(root, text="Moving image", padx=10, pady=5, fg="white",
                                           bg="#263D42", command=add_image(1, moving_frame))

    choose_fixed_image_button.pack()
    choose_moving_image_button.pack()

    root.mainloop()


if __name__ == "__main__":
    run_app()
