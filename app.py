import os
import tkinter as tk
from tkinter import BOTH, BOTTOM, LEFT, NE, NW, RIGHT, TOP, VERTICAL, X, Y, Canvas, Scrollbar, filedialog, Text
from matplotlib.figure import Figure
import math
import gui

import numpy as np
import registration
# from PIL import ImageTk, Image
import SimpleITK as sitk
import matplotlib.pylab as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

FIX_IDX = 0
MOV_IDX = 0

points_list = []
transformed_points_list = []
first_chart_results = []
second_chart_results =[]

HIST_SIZE = 0

class GradientData:
    def __init__(self) -> None:
        self.learningRate=tk.StringVar(value=0.01)
        self.numberOfIterations=tk.StringVar(value=50)
        self.convergenceMinimumValue=tk.StringVar(value=1e-6)
        self.convergenceWindowSize=tk.StringVar(value=20)

class StepGradientData:
    def __init__(self) -> None:
        self.learningRate=tk.StringVar(value=5)
        self.numberOfIterations=tk.StringVar(value=10)
        self.minStep=tk.StringVar(value=0.01)

class LBFGSBData:
    def __init__(self) -> None:
        self.numberOfIterations=tk.StringVar(value=50)
        self.gradientConvergenceTolerance = tk.StringVar(value="1e-5")


# def update_metric(new_value):
class App():
    def __init__(self) -> None:
        self.images = ["None", "None"]
        self.root = tk.Tk()
        self.metric = tk.StringVar()#(self.root, value='run registration to see results')
        self.metric.set('run registration to see results')
        self.interpolation = tk.StringVar(value=registration.interpolation_options[0])
        self.sampling_percentage = tk.StringVar(value='0.01')
        self.sampling_strategy = tk.StringVar(value=registration.sampling_strategies[0])
        self.bins = tk.IntVar(value=10)
        self.optimizer = tk.StringVar(value=registration.optimizers[0])
        self.opt_frame_list = None
        self.transform_file = tk.StringVar(value='(transform file is optional)')
        self.new_transform_file = tk.StringVar(value='output/ct2mrT1')
        self.res_fig = Figure(figsize = (4, 3), dpi = 100)
        self.plot1 = self.res_fig.add_subplot(111)
        self.moving_frame = None
        self.moving_image = None
        self.chess = None
        self.canvas_res = None
        self.deform = tk.StringVar(value=registration.deformable_regist[1])

        self.mean = tk.StringVar(value='0')
        self.std = tk.StringVar(value='0')
        self.chess_frame = None
        self.build_gui()


    def transform_point(self, point):
        transform = sitk.ReadTransform(self.transform_file.get())
        transformed_point = transform.TransformPoint(point)
        return transformed_point

    def add_image(self, idx, frame):
        file_name = filedialog.askopenfilename(initialdir=os.path.abspath(os.getcwd())+"/data", title="Select Image")
        self.images[idx] = file_name
        if idx == 1:
            self.moving_image = file_name
            self.moving_frame = frame

        self.create_working_img(file_name, frame)
    

    def add_file(self):
        file_name = filedialog.askopenfilename(initialdir=os.path.abspath(os.getcwd()), title="Select Transform file")
        self.transform_file.set(file_name)

    def run_registration(self):
        # image = ImageTk.PhotoImage(Image.open(os.path.abspath(os.getcwd())+"\\output\\iteration000.jpg"))
        if self.canvas_res == None:
            self.canvas_res = Canvas(self.result_frame, bg="Black", width=self.result_frame.winfo_width(), height=self.result_frame.winfo_height())
            self.canvas_res.pack()

            self.result_label = tk.Label(self.canvas_res)
            self.canvas_res.create_window(0, 0, window=self.result_label, anchor=NW)

            vbar=Scrollbar(self.canvas_res, orient=VERTICAL, command=self.canvas_res.yview)
        # vbar.pack(side=RIGHT,fill=Y)
            vbar.place(relx=1, rely=0, relheight=1, anchor=NE)
            self.canvas_res.config(yscrollcommand=vbar.set, scrollregion=(0, 0, 0, 900))

        # self.result_label.pack(expand=True)
        # self.chess = 0

        if float(self.sampling_percentage.get()) > 1:
            self.sampling_percentage.set('1.0')
        
        self.metric.set('initializing registration...')
        registration.register(self.images[0], self.images[1], self, self.interpolation.get(), self.sampling_percentage.get(), 
                                self.sampling_strategy.get(), self.bins.get(), self.optimizer.get(), self.opt_data, self.new_transform_file.get(),
                                self.deform.get())

    def calculate_hist_values(self, chart_results):
        n, bins = np.histogram(chart_results)
        mids = 0.5 * (bins[1:] + bins[:-1])
        my_mean = np.average(mids, weights=n)

        self.mean.set(str(my_mean))
        var = np.average((mids - my_mean) ** 2, weights=n)
        self.std.set(str(np.sqrt(var)))

    def show_results_old(self, chart_results, color):
        self.calculate_hist_values(chart_results)
        num_bins = 50
        self.plot1.clear()
        self.plot1.hist(chart_results, num_bins, range=(0, max(first_chart_results)), facecolor=color, alpha=0.5)
        #n_2, bins_2, patches_2 = self.plot1.hist(second_chart_results, num_bins, facecolor='blue', alpha=0.5)
        self.canvas.draw()
        self.fig_toolbar.update()

    def show_results(self, x, y):
        self.plot1.clear()
        self.plot1.plot(x, y)
        self.canvas.draw()
        self.fig_toolbar.update()


    def show_chess(self, fixed, moving):
         #chessboard
        from PIL import Image
        chess_result = sitk.GetArrayFromImage(sitk.CheckerBoard(fixed, moving, [11, 8, 4]))

        if chess_result is not None and self.chess_frame is not None:
            IDX = 0
            def update_image(IDX):
                for widget in self.chess_frame.winfo_children():
                    widget.destroy()

                fig, ax = plt.subplots(figsize=(20, 12))
                img = chess_result[int(IDX), :, :]
                plt.imshow(img, cmap='gray_r')
                canvas_figure = FigureCanvasTkAgg(fig, master=self.chess_frame)
                canvas_figure.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

            update_image(0)

            if self.chess is None:
                chess_arr = (chess_result)
                # scale = self.display.slicer_box
                scale = tk.Scale(self.right_frame, from_=0, to=len(chess_arr) - 1, label="Chessboard", length=len(chess_arr), orient='horizontal',
                                command=update_image)
                scale.pack(pady=5)

            self.chess = chess_result


    def update_result_image(self, number, chess_result=None):
        #self.image = ImageTk.PhotoImage(Image.open(os.path.abspath(os.getcwd())+"/output/iteration{0}.jpg".format(number)))
        print(number, os.path.abspath(os.getcwd())+"/output/iteration{0}.jpg".format(number))
        
        #self.result_label.configure(image=self.image, text='iteration: '+str(number), compound='top')


    def calculate_distance(self, point_1, point_2):

        print("  ")
        print("point 1 ", point_1)
        print("point 2 ", point_2)

        print("distance ", str(math.dist(point_1, point_2)))
        return math.dist(point_1, point_2)


    def create_distance_list(self):

        i = 0
        while i != len(points_list):
            distance = self.calculate_distance(points_list[i], points_list[i + 1])
            first_chart_results.append(distance)
            i = i + 2

        fixed_points = points_list[::2]
        i = 0
        for point_1 in fixed_points:
            point_2 = transformed_points_list[i]
            distance = self.calculate_distance(point_1, point_2)
            second_chart_results.append(distance)
            i = i + 1
    # fixed/moving mhd photo

    def draw_moving_image_points(self):
        frame = self.moving_frame
        IDX = FIX_IDX
        file_name = self.moving_image
        for widget in frame.winfo_children():
            widget.destroy()

        points_to_be_drawn = points_list[::2]
        itk_image = sitk.ReadImage(file_name, sitk.sitkFloat32)
        image_array = sitk.GetArrayViewFromImage(itk_image)
        fig = plt.figure(figsize=(5, 4))

        for point in points_to_be_drawn:
            result_point = self.transform_point(point)
            transformed_points_list.append(result_point)
            plt.plot(result_point[0], result_point[1], 'ro', markersize=4)
            fig.canvas.draw()

        plt.imshow(image_array[int(IDX)], cmap='Greys_r')
        canvas_figure = FigureCanvasTkAgg(fig, master=frame)
        canvas_figure.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.create_distance_list()
        #x = [x for x in range(len(first_chart_results))]
        #self.show_results()

    def update_moving_image(self, file_name, frame, IDX, point):
        for widget in frame.winfo_children():
            widget.destroy()

        itk_image = sitk.ReadImage(file_name, sitk.sitkFloat32)
        image_array = sitk.GetArrayViewFromImage(itk_image)
        fig = plt.figure(figsize=(5, 4))

        def mouse_event(event):
            plt.plot(event.xdata, event.ydata, 'ro', markersize=4)
            fig.canvas.draw()
            current_point = (event.xdata, event.ydata, 0)
            #point = self.transform_point(current_point)
            points_list.append(current_point)

        fig.canvas.mpl_connect('button_press_event', mouse_event)
        plt.plot(point[0], point[1], 'ro', markersize=4)
        fig.canvas.draw()
        plt.imshow(image_array[int(IDX)], cmap='Greys_r')
        canvas_figure = FigureCanvasTkAgg(fig, master=frame)
        canvas_figure.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def create_working_img(self, file_name, frame):
        itk_image = sitk.ReadImage(file_name, sitk.sitkFloat32)
        image_array = sitk.GetArrayViewFromImage(itk_image)

        def update_image(IDX):
            for widget in frame.winfo_children():
                widget.destroy()

            itk_image = sitk.ReadImage(file_name, sitk.sitkFloat32)
            image_array = sitk.GetArrayViewFromImage(itk_image)
            fig = plt.figure(figsize=(5, 4))
            self.FIX_IDX = IDX

            def mouse_event(event):
                plt.plot(event.xdata, event.ydata, 'ro', markersize=4)
                fig.canvas.draw()
                current_point = (event.xdata, event.ydata, 0)
                points_list.append(current_point)

            fig.canvas.mpl_connect('button_press_event', mouse_event)
            plt.imshow(image_array[int(IDX)], cmap='Greys_r')
            canvas_figure = FigureCanvasTkAgg(fig, master=frame)
            canvas_figure.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        update_image(0)

        # slider
        scale = tk.Scale(self.middle_frame, from_=0, to=len(image_array) - 1, label=file_name.split('/')[-1], length=len(image_array), orient='horizontal',
                            command=update_image)
        scale.pack(pady=5)


    def change_optimizer_fields(self, *args):
        if self.opt_frame_list != None:
            for frame in self.opt_frame_list:
                for widgets in frame.winfo_children():
                    widgets.destroy()
                frame.destroy()
        # else:
        #     self.opt_frame = tk.Frame(self.right_frame)
        #     self.opt_frame.pack(fill=X)
        
        self.opt_frame_list = []
        if self.optimizer.get() in ['GradientDescent', 'GradientDescentLineSearch', 'ConjugateGradientLineSearch']:
            self.opt_data = GradientData()
        elif self.optimizer.get()=='RegularStepGradientDescent':
            self.opt_data = StepGradientData()
        elif self.optimizer.get() == 'LBFGSB':
            self.opt_data = LBFGSBData()

        for attr, value in self.opt_data.__dict__.items():
            opt_frame = tk.Frame(self.opt_params_frame)
            opt_frame.pack(fill=X)
            lbl = tk.Label(opt_frame, text=str(attr), width=25)
            lbl.pack(side=LEFT, padx=3, pady=5)
            drop = tk.Entry(opt_frame, textvariable=getattr(self.opt_data, attr), width=10)
            drop.pack(pady=5)
            self.opt_frame_list.append(opt_frame)




    def build_gui(self):

        # main frame - is divided into two columns: left one has images, in right one are buttons etc.
        # right-right part has results
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=X)

        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(fill=BOTH, side=LEFT)

        self.middle_frame = tk.Frame(self.main_frame)
        self.middle_frame.pack(fill=BOTH, side=LEFT, pady=(40, 5))

        self.right_frame = tk.Frame(self.main_frame) 
        self.right_frame.pack(fill=BOTH, side=RIGHT, pady=(40, 5))


        canvas = tk.Canvas(self.left_frame, height=850, width=710, bg="#263D42")
       
        # canvas.config(yscrollcommand=vbar.set)
        canvas.pack()

        # Fixed frame
        fixed_frame = tk.Frame(self.left_frame, bg="white")
        fixed_frame.place(relwidth=0.5, relheight=0.30)

        # Moving frame
        moving_frame = tk.Frame(self.left_frame, bg="white")
        moving_frame.place(relwidth=0.5, relheight=0.30, relx=0.5, rely=0)

        self.result_frame = tk.Frame(self.left_frame, bg='black')
        self.result_frame.place(relheight=0.7, relwidth=0.45, relx=0.25, rely=0.30)


        # buttons
        btn_frame = tk.Frame(self.middle_frame)
        btn_frame.pack(fill=X)
        choose_fixed_image_button = tk.Button(btn_frame, text="Fixed image", padx=10, pady=5, fg="white",
                                            bg="#263D42", command=lambda: self.add_image(0, fixed_frame))

        choose_moving_image_button = tk.Button(btn_frame, text="Moving image", padx=10, pady=5, fg="white",
                                            bg="#263D42", command=lambda: self.add_image(1, moving_frame))

    
        choose_fixed_image_button.pack(side=LEFT, pady=5, padx=20)
        choose_moving_image_button.pack(pady=5)


        # transform file
        transform_frame = tk.Frame(self.middle_frame)
        transform_frame.pack(fill=X)
        transform_lbl = tk.Button(transform_frame, text="Transform file", padx=10, pady=5, fg="white",
                                            bg="#263D42", command=lambda: self.add_file())
        transform_lbl.pack(side=LEFT, padx=15, pady=5)
        drop = tk.Entry(transform_frame, textvariable=self.transform_file, width=30)
        drop.pack(pady=13)
                    # jak się wybierze plik transformaty to on jest zapisany w zmiennej self.transform_file

        # interpolation method dropdown
        interpolation_frame = tk.Frame(self.middle_frame)
        interpolation_frame.pack(fill=X)
        interpolation_lbl = tk.Label(interpolation_frame, text="Interpolation method: ", width=20)
        interpolation_lbl.pack(side=LEFT, padx=3, pady=5)
        drop = tk.OptionMenu(interpolation_frame, self.interpolation , *registration.interpolation_options)
        drop.pack(pady=5)

        # number of histogram bins
        bins_frame = tk.Frame(self.middle_frame)
        bins_frame.pack(fill=X)
        bins_lbl = tk.Label(bins_frame, text="Number of histogram bins ", width=20)
        bins_lbl.pack(side=LEFT, padx=5, pady=5)
        bins_drop = tk.Entry(bins_frame, textvariable=self.bins, width=10)
        bins_drop.pack(pady=5)

        # sampling percentage field
        percent_frame = tk.Frame(self.middle_frame)
        percent_frame.pack(fill=X)
        percent_lbl = tk.Label(percent_frame, text="Sampling Percentage (0,1]: ", width=20)
        percent_lbl.pack(side=LEFT, padx=5, pady=5)
        percent = tk.Entry(percent_frame, textvariable=self.sampling_percentage , width=10)
        percent.pack(pady=5)


        # sampling strategy field
        strategy_frame = tk.Frame(self.middle_frame)
        strategy_frame.pack(fill=X)
        strategy_lbl = tk.Label(strategy_frame, text="Sampling Strategy: ", width=20)
        strategy_lbl.pack(side=LEFT, padx=5, pady=5)
        strategy_drop = tk.OptionMenu(strategy_frame, self.sampling_strategy, *registration.sampling_strategies)
        strategy_drop.pack(pady=5)

        # optimizer field
        opt_frame = tk.Frame(self.middle_frame)
        opt_frame.pack(fill=X)

        opt_frame1 = tk.Frame(opt_frame)
        opt_frame1.pack(fill=X, side=TOP)
        opt_lbl = tk.Label(opt_frame1, text="Optimalizer options: ", width=20)
        opt_lbl.pack(side=LEFT, padx=5, pady=5)
        opt_drop = tk.OptionMenu(opt_frame1, self.optimizer, *registration.optimizers)
        opt_drop.pack(pady=(10,5))
        self.optimizer.trace('w', self.change_optimizer_fields)

        self.opt_params_frame = tk.Frame(opt_frame)
        self.opt_params_frame.pack(fill=X, side=BOTTOM)
        self.change_optimizer_fields()

        # transform file save
        interpolation_frame = tk.Frame(self.middle_frame)
        interpolation_frame.pack(fill=X)
        interpolation_lbl = tk.Label(interpolation_frame, text="Transform file name:", width=20)
        interpolation_lbl.pack(side=LEFT, padx=5, pady=5)
        drop = tk.Entry(interpolation_frame, textvariable= self.new_transform_file, width=35)
        drop.pack(pady=5)

        # second-step transform
        deform_frame = tk.Frame(self.middle_frame)
        deform_frame.pack(fill=X)

        deform_lbl1 = tk.Label(deform_frame, text="Deformable registration: ", width=22)
        deform_lbl1.pack(side=LEFT, padx=5, pady=5)
        def_drop = tk.OptionMenu(deform_frame, self.deform, *registration.deformable_regist)
        def_drop.pack(pady=(10,5))

        # registration button

        frame1 = tk.Frame(self.middle_frame)
        frame1.pack(fill=X)
        run_button = tk.Button(frame1, text="Run simple registration", padx=10, pady=5, fg="white",
                            bg="#263D42", command=self.run_registration)
        run_button.pack(side=LEFT, pady=(10,5))



        point_button = tk.Button(frame1, text="Transform points", padx=10, pady=5, fg="white",
                            bg="#263D42", command=self.draw_moving_image_points)

        point_button.pack(side=RIGHT,pady=(10,5))
        # metrices results
        frame1 = tk.Frame(self.middle_frame)
        frame1.pack(fill=X)

        lbl1 = tk.Label(frame1, text="Metric value: ", width=10)
        lbl1.pack(side=LEFT, padx=5, pady=5)

        entry1 = tk.Entry(frame1, state='disabled', textvariable=self.metric, width=35)
        entry1.pack(fill=X, padx=5, pady=5, expand=False)

        # hist buttons

        hist_button_frame = tk.Frame(self.middle_frame)
        hist_button_frame.pack(fill=X)
        fixed_hist = tk.Button(hist_button_frame, text="Manual hist", padx=10, pady=5, fg="white",
                                              bg="#263D42", command=lambda: self.show_results_old(first_chart_results, 'red'))

        trans_hist = tk.Button(hist_button_frame, text="Trans hist", padx=10, pady=5, fg="white",
                                               bg="#263D42", command=lambda: self.show_results_old(second_chart_results, 'blue'))

        fixed_hist.pack(side=LEFT, pady=5, padx=20)
        trans_hist.pack(side=RIGHT, pady=5)


        #results_info  dziala
        frame1 = tk.Frame(self.right_frame)
        frame1.pack(fill=X)

        lbl1 = tk.Label(frame1, text="Mean: ", width=10)
        lbl1.pack(side=LEFT, padx=3, pady=3)

        entry1 = tk.Entry(frame1, state='disabled', textvariable=self.mean, width=15)
        entry1.pack(fill=X, padx=3, pady=3, expand=False)
        frame1 = tk.Frame(self.right_frame)
        frame1.pack(fill=X)
        lbl1 = tk.Label(frame1, text="Std: ", width=10)
        lbl1.pack(side=LEFT, padx=3, pady=3)

        entry1 = tk.Entry(frame1, state='disabled', textvariable=self.std, width=15)
        entry1.pack(fill=X, padx=3, pady=3, expand=False)

        frame1 = tk.Frame(self.right_frame)
        frame1.pack(fill=X)
        self.canvas = FigureCanvasTkAgg(self.res_fig, master=frame1)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=X, side=TOP, padx=5, pady=5)
        self.fig_toolbar = NavigationToolbar2Tk(self.canvas, frame1)
        self.fig_toolbar.update()
        self.canvas.get_tk_widget().pack(fill=X, side=TOP, padx=5, pady=5)

        self.chess_frame = tk.Frame(self.right_frame, bg='black')
        self.chess_frame.place(relheight=0.35, relwidth=1, relx=0.05, rely=0.55)
        self.chess_label = tk.Label(self.chess_frame)
        self.chess_label.pack()

        self.root.mainloop()



    def set_metric(self, value):
        self.metric.set(value)



if __name__ == "__main__":
    app = App()
    # run_app()