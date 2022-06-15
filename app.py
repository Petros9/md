import os
import tkinter as tk
from tkinter import BOTH, LEFT, RIGHT, X, filedialog, Text

from pygame import init
import registration
from PIL import ImageTk, Image
import SimpleITK as sitk
import matplotlib.pylab as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

FIX_IDX = 0

MOV_IDX = 0


# def update_metric(new_value):
class App():
    def __init__(self) -> None:
        self.images = ["None", "None"]
        self.root = tk.Tk()
        self.metric = tk.StringVar()#(self.root, value='run registration to see results')
        self.metric.set('run registration to see results')
        
        self.build_gui()


    def add_image(self, idx, frame):
        file_name = filedialog.askopenfilename(initialdir=os.path.abspath(os.getcwd())+"\\data", title="Select Image")
        self.images[idx] = file_name
        self.create_working_img(file_name, frame)
    

    def run_registration(self):
        # image = ImageTk.PhotoImage(Image.open(os.path.abspath(os.getcwd())+"\\output\\iteration000.jpg"))
        self.result_label = tk.Label(self.result_frame)
        self.result_label.pack()
        registration.register(self.images[0], self.images[1], self)

    def update_result_image(self, number):
        self.image = ImageTk.PhotoImage(Image.open(os.path.abspath(os.getcwd())+"\\output\\iteration{0}.jpg".format(number)))
        print(number, os.path.abspath(os.getcwd())+"\\output\\iteration{0}.jpg".format(number))
        
        self.result_label.configure(image=self.image, text='iteration: '+str(number), compound='bottom')


    # fixed/moving mhd photo
    def create_working_img(self, file_name, frame):
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

        # slider
        scale = tk.Scale(self.right_frame, from_=0, to=len(image_array) - 1, label=file_name.split('/')[-1], length=len(image_array), orient='horizontal',
                            command=update_image)
        scale.pack(pady=5)


    def build_gui(self):

        # main frame - is divided into two columns: left one has images, in right one are buttons etc.
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=X)

        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(fill=BOTH, side=LEFT)

        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.pack(fill=BOTH, side=RIGHT, pady=(40, 5))


        canvas = tk.Canvas(self.left_frame, height=700, width=700, bg="#263D42")
        canvas.pack()

        # Fixed frame
        fixed_frame = tk.Frame(self.left_frame, bg="white")
        fixed_frame.place( relwidth=0.5, relheight=0.30)

        # Moving frame
        moving_frame = tk.Frame(self.left_frame, bg="white")
        moving_frame.place( relwidth=0.5, relheight=0.30, relx=0.5, rely=0)

        self.result_frame = tk.Frame(self.left_frame, bg='black')
        self.result_frame.place(relheight=0.7, relwidth=0.5, relx=0.25, rely=0.30)


        # buttons
        btn_frame = tk.Frame(self.right_frame)
        btn_frame.pack(fill=X)
        choose_fixed_image_button = tk.Button(btn_frame, text="Fixed image", padx=10, pady=5, fg="white",
                                            bg="#263D42", command=lambda: self.add_image(0, fixed_frame))

        choose_moving_image_button = tk.Button(btn_frame, text="Moving image", padx=10, pady=5, fg="white",
                                            bg="#263D42", command=lambda: self.add_image(1, moving_frame))

    
        choose_fixed_image_button.pack(side=LEFT, pady=5, padx=20)
        choose_moving_image_button.pack(pady=5)

        # registration button
        run_button = tk.Button(self.right_frame, text="Run simple registration", padx=10, pady=5, fg="white",
                            bg="#263D42", command=self.run_registration)
        run_button.pack(pady=(10,5))

        # metrices results
        frame1 = tk.Frame(self.right_frame)
        frame1.pack(fill=X)

        lbl1 = tk.Label(frame1, text="Metric value: ", width=10)
        lbl1.pack(side=LEFT, padx=5, pady=5)

        entry1 = tk.Entry(frame1, state='disabled', textvariable=self.metric, width=35)
        entry1.pack(fill=X, padx=5, pady=5, expand=False)

        self.root.mainloop()


    def set_metric(self, value):
        self.metric.set(value)



        # def create_working_img(self, file_name, frame):
        #     itk_image = sitk.ReadImage(file_name, sitk.sitkFloat32)
        #     image_array = sitk.GetArrayViewFromImage(itk_image)

        #     def update_image(IDX):
        #         for widget in frame.winfo_children():
        #             widget.destroy()

        #         itk_image = sitk.ReadImage(file_name, sitk.sitkFloat32)
        #         image_array = sitk.GetArrayViewFromImage(itk_image)
        #         fig = plt.figure(figsize=(5, 4))
        #         print(IDX)
        #         plt.imshow(image_array[int(IDX)], cmap='Greys_r')
        #         canvas_figure = FigureCanvasTkAgg(fig, master=frame)
        #         canvas_figure.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        #     update_image(0)

        #     # slider
        #     scale = tk.Scale(self.root, from_=0, to=len(image_array) - 1, label=file_name.split('/')[-1], length=len(image_array), orient='horizontal',
        #                         command=update_image)
        #     scale.pack()





# def add_image(idx, frame):
#     file_name = filedialog.askopenfilename(initialdir=os.path.abspath(os.getcwd())+"\\data", title="Select Image")
#     images[idx] = file_name
#     create_working_img(file_name, frame)
    

# def run_registration():
#     image = ImageTk.PhotoImage(Image.open(os.path.abspath(os.getcwd())+"\\output\\iteration000.jpg"))
#     label = tk.Label(result_frame, image=image)
#     label.pack()
#     registration.register(images[0], images[1], label, metric_val)

# def run_app():
#     # front
#     images = ["None", "None"]

#     root = tk.Tk()

#     canvas = tk.Canvas(root, height=500, width=700, bg="#263D42")
#     canvas.pack(padx=10, pady=10)

#     # Fixed frame
#     fixed_frame = tk.Frame(root, bg="white")
#     fixed_frame.place(relwidth=0.5, relheight=0.25)

#     # Moving frame
#     moving_frame = tk.Frame(root, bg="white")
#     moving_frame.place(relwidth=0.5, relheight=0.25, relx=0.5, rely=0)

#     result_frame = tk.Frame(root, bg='black')
#     result_frame.place(relheight=0.375, relwidth=0.5, relx=0.25, rely=0.30)

#     choose_fixed_image_button = tk.Button(root, text="Fixed image", padx=10, pady=5, fg="white",
#                                           bg="#263D42", command=lambda: add_image(0, fixed_frame))

#     choose_moving_image_button = tk.Button(root, text="Moving image", padx=10, pady=5, fg="white",
#                                            bg="#263D42", command=lambda: add_image(1, moving_frame))

#     choose_fixed_image_button.pack()
#     choose_moving_image_button.pack()

#     run_button = tk.Button(root, text="Run simple registration", padx=10, pady=5, fg="white",
#                            bg="#263D42", command=run_registration)

#     run_button.pack()

#     # metrices
#     metric_val = tk.StringVar(root, value='run registration to see results')
#     frame1 = tk.Frame(root)
#     frame1.pack(fill=X)

#     lbl1 = tk.Label(frame1, text=" Metric value: ", width=6)
#     lbl1.pack(side=LEFT, padx=5, pady=5)

#     entry1 = tk.Entry(frame1, state='disabled', textvariable=metric_val)
#     entry1.pack(fill=X, padx=5, expand=False)

#     root.mainloop()


if __name__ == "__main__":
    app = App()
    # run_app()