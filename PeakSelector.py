import numpy as np
import pandas as pd
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
from matplotlib.widgets import Button


class PeakSelector:
    def __init__(self,filename):
        
        #read data
        self.filename = filename
        self.data = pd.read_csv(filename)
        self.frame = 1
        self.current_data = self.data[self.data['Frame'] == self.frame] #frame=1のデータの取り出す
        self.x = np.array(self.current_data['Wavelength'])
        self.y = np.array(self.current_data['Intensity'])
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.ax.plot(self.x, self.y, '-r', label='Intensity')
        self.ax.set_xlabel('Wavelength (nm)')
        self.ax.set_ylabel('Intensity')
        
        #フレーム毎に選択された点を保存する
        self.selected_x = []
        self.selected_y = []
        self.selected_points = None
        
        #peaks
        peaks = find_peaks(self.y, height=0)
        self.x_peaks = self.x[peaks[0]]
        self.y_peaks = self.y[peaks[0]]
        self.ax.plot(self.x_peaks, self.y_peaks, 'x', color='black', markersize=5)

        #candidate, → or clickで移動してハイライトする
        self.candidate_i  = 0
        self.candidate_x = [self.x_peaks[0]]
        self.candidate_y = [self.y_peaks[0]]
        self.current_point = None
        #self.ax.plot(self.candidate_x, self.candidate_y, 'o', color='yellow', markersize=20, alpha=0.5)
        
        #最終的にoutputするデータ
        self.saved_x = []
        self.saved_frame = []
        
        #フレーム番号を表示する
        self.frame_number_textbox = self.ax.text(0.95, 0.95, f"Frame: {self.frame}", transform=self.ax.transAxes, va="top", ha="right", bbox=dict(facecolor='white', alpha=0.7))
        self.explanation_textbox = self.ax.text(0.95, 0.8, "c: choose, d: delete", transform=self.ax.transAxes, va="top", ha="right")

        
        self.textbox = self.ax.text(0.75, 0.95, '', transform=self.ax.transAxes, va="top", ha="right", bbox=dict(facecolor='white', alpha=0.7))
        self.cid_click = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        self.cid_motion = self.fig.canvas.mpl_connect('motion_notify_event', self.onmotion)
        self.cid_key = self.fig.canvas.mpl_connect('key_press_event', self.onkey) #キーボードイベントのハンドラを追加

        ax_save = plt.axes([0.9, 0.02, 0.08, 0.04])
        self.btn_save = Button(ax_save, 'Save', color='lightblue', hovercolor='0.975')
        self.btn_save.on_clicked(self.save_data)
        
        ax_delete = plt.axes([0.8, 0.02, 0.08, 0.04])
        self.btn_delete = Button(ax_delete, 'Delete', color='gray', hovercolor='0.975')
        self.btn_delete.on_clicked(self.delete_data)
        
        ax_next = plt.axes([0.7, 0.02, 0.08, 0.04])
        self.btn_next = Button(ax_next, 'Next', color='green', hovercolor='0.975')
        self.btn_next.on_clicked(self.next_frame)

    def onclick(self, event):
        if event.inaxes != self.ax:
            return
        # 最も近いデータ点のy座標を取得
        closest_i = np.abs(self.x_peaks - event.xdata).argmin()
        
        #candidateをハイライトする
        self.candidate_i = closest_i
        self.update_candidate()
        
        #選択した点を表示する
        if self.selected_points:
            self.selected_points.remove()
        self.selected_points = self.ax.scatter(self.selected_x, self.selected_y,facecolors='none', edgecolors='black', marker='o',s=30)
        
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()


    def onmotion(self, event):
        """モーションイベントのハンドラ"""
        if event.inaxes == self.ax:
            self.textbox.set_text(f"x={event.xdata:.2f}, y={event.ydata:.2f}")
            self.fig.canvas.draw()

    def onkey(self, event):
        """キーボードイベントのハンドラ"""
        if event.key == 'c':
            #output arrayに保存する
            self.selected_x.append(self.x_peaks[self.candidate_i])
            self.selected_y.append(self.y_peaks[self.candidate_i])
            if self.selected_points:
                self.selected_points.remove()
            self.selected_points = self.ax.scatter(self.selected_x, self.selected_y,facecolors='none', edgecolors='black', marker='o',s=30)
                    
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
        elif event.key == "right":
            self.candidate_i +=1
            self.update_candidate()
        elif event.key == "left":
            self.candidate_i += -1
            self.update_candidate()
        elif event.key == "d":
            if self.selected_x:
                self.selected_x.pop()
                self.selected_y.pop()
            print(self.selected_x)
            if self.selected_points:
                self.selected_points.remove()
            self.selected_points = self.ax.scatter(self.selected_x, self.selected_y,facecolors='none', edgecolors='black', marker='o',s=30)
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
    
    def next_frame(self,event):
        
        #前のフレームで選択された点をsaved_xに保存する
        self.saved_x = self.saved_x + self.selected_x
        self.saved_frame = self.saved_frame + [self.frame]*len(self.selected_x)
        #前のフレームで選択された点を削除する
        self.selected_x = []
        self.selected_y = []
        #if self.selected_points:
                #self.selected_points.remove()
        
        #新しいフレームのデータを取り出す
        if self.frame < self.data['Frame'].max():
            self.frame +=1
        else:
            print("次のフレームはありません")
        self.current_data = self.data[self.data['Frame'] == self.frame] #self.frameのデータの取り出す
        self.x = np.array(self.current_data['Wavelength'])
        self.y = np.array(self.current_data['Intensity'])
        
        self.ax.clear()
        self.ax.plot(self.x, self.y, '-r', label='Intensity')
        
        #peaks
        peaks = find_peaks(self.y, height=0)
        self.x_peaks = self.x[peaks[0]]
        self.y_peaks = self.y[peaks[0]]
        self.ax.plot(self.x_peaks, self.y_peaks, 'x', color='black', markersize=5)
        
        self.frame_number_textbox = self.ax.text(0.95, 0.95, f"Frame: {self.frame}", transform=self.ax.transAxes, va="top", ha="right", bbox=dict(facecolor='white', alpha=0.7))
        self.explanation_textbox = self.ax.text(0.95, 0.8, "c: choose, d: delete", transform=self.ax.transAxes, va="top", ha="right")
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    
    #candidate pointをself.candidate_iを元に更新し, ハイライトする
    def update_candidate(self):
        if self.current_point:
                self.current_point.remove()
        self.candidate_x = self.x_peaks[self.candidate_i]
        self.candidate_y = self.y_peaks[self.candidate_i]
        self.current_point = self.ax.scatter([self.candidate_x],[self.candidate_y], color='yellow', marker='o', s=80, alpha=0.5)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    
    #選択されたデータポイントの最後を1つ削除する
    def delete_data(self, event):
        if self.selected_x:
            self.selected_x.pop()
            self.selected_y.pop()
            print(self.selected_x)
        if self.selected_points:
            self.selected_points.remove()
        self.selected_points = self.ax.scatter(self.selected_x, self.selected_y,facecolors='none', edgecolors='black', marker='o',s=30)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    
    def save_data(self, event):
        #selected_xが空でない場合にsaved_xに追加する
        if self.selected_x:
            #選択された点をsaved_xに保存する
            self.saved_x = self.saved_x + self.selected_x
            self.saved_frame = self.saved_frame + [self.frame]*len(self.selected_x)
            #選択された点を削除する
            self.selected_x = []
            self.selected_y = []
        
        """選択されたデータポイント(saved_x)を.datファイルに保存する関数"""
        output_filename = self.filename.replace(".csv", "_selected.dat")
        with open(output_filename, "w") as f:
            for fr, x in zip(self.saved_frame, self.saved_x):
                f.write(f"{fr} {x}\n")
        print(f"Data saved to {output_filename}")

    def show(self):
        """GUIを表示する関数"""
        plt.show()