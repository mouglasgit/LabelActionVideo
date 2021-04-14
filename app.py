# -*- coding: utf-8 -*-

import PIL.Image
# import Image
# import PIL 
from Tkinter import *  
import PIL.ImageTk as ImageTk


import os
import cv2
import json
import shutil 
import numpy as np
import threading


SIZE_W, SIZE_H = 1400, 850


class TKMarkCoorAnnotation(Frame):

    def __init__(self):
        
        self.dist1 = np.Inf
        self.dist2 = np.Inf
        self.TDIST = 4
        
        #inputs-------------------        
        input_data = self.load_config()

        self.switch_class = self.parse_index(input_data['class'])

        img_input = input_data['dataset']['inputs']
        img_data = input_data['dataset']['outputs']
        img_anotation = input_data['dataset']['anotations']

        self.path_input = img_input
        self.path_save_img = img_data
        self.path_save_anotation = img_anotation
        
        #----------------------------------------------------------------
        
        self.id = 0
        self.idImag = 0
        self.idImagGlobal = 0
        self.angulo = 0
        self.frame = None
        
        global SIZE_W, SIZE_H
        
        self.size_w, self.size_h = SIZE_W, SIZE_H
        
    
        self.videos = [name for name in os.listdir(self.path_input) if os.path.isfile(self.path_input + name)]
        self.videos = sorted(self.videos)
        
        
        self.capture = None
        self.start_video = False
        self.id_frame = 0
        self.DURATION = 8
        
        
        print self.videos
        
        
        self.drawing = False  # true if mouse is pressed
        self.mode = True
        
        self.arquivo = open('info.txt', 'w')
        self.salvar = ""
        
        self.name_img = None
        
        self.objetos_coo = []
        self.objetos_re_draw = []
        
        self.copy_objetos_coo = []
        self.copy_objetos_re_draw = []
        
        self.copy_selec_objeto_coo = None
        self.copy_selec_objeto_re_draw = None
        
        self.classe_info()
        
        #---------------------------------------------------------------------
        Frame.__init__(self, master=None, bg='black')
        self.x1, self.y1 = 0, 0
        self.x2, self.y2 = 0, 0
        
        self.canvas = Canvas(self, cursor="cross")
        self.canvas.place(x=160, y=140, width=self.size_w, height=self.size_h)

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<Motion>", self.on_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        
        self.master.bind("<KeyPress>", self.key_press)
        
        self.rect = None

        self.start_x = None
        self.start_y = None

        #---------------------------------------------
        
        label_files = Label(self, text="Arquivos", bg='black', fg="white", font=("Arial", 14))
        label_files.place(x=30, y=20)
        
        #------------------
        
        self.list_files = Listbox(self, selectmode=SINGLE, exportselection=False, bg='black', fg="white")
        for item in self.videos:
            self.list_files.insert(END, item)
        self.list_files.bind('<<ListboxSelect>>', self.file_item_select)
        #-----------------
        self.list_files.select_set(0)
        
        scrollbar = Scrollbar(self.list_files)
        scrollbar.config(command=self.list_files.yview)
        scrollbar.pack(side="right", fill="y")
        self.list_files.config(yscrollcommand=scrollbar.set) 
        self.list_files.place(x=10, y=50, width=140, height=640)
        #-------------------------------------------------------------
        
        #---------------------------------------------------------------------
        
        label_list = Label(self, text="Classes", bg='black', fg="white", font=("Arial", 14))
        label_list.place(x=self.size_w + 180, y=20)
        
        #------------------
        
        self.listbox = Listbox(self, selectmode=SINGLE, exportselection=False, bg='black', fg="white")
        for item in self.switch_class:
            self.listbox.insert(END, self.switch_class[item])
        # self.listbox.place(x=10, y=480, width=80, height=40)
        self.listbox.bind('<<ListboxSelect>>', self.class_item_select)
        #-----------------
        self.listbox.select_set(0)
        
        scrollbar = Scrollbar(self.listbox)
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set) 
        self.listbox.place(x=self.size_w + 170, y=50, width=140, height=320)
        # self.listbox.place(x=10, y=140, width=140, height=self.size_h)
        #-------------------------------------------------------------
        
        self.classe = self.switch_class[self.switch_class.keys()[0]]
        
    
        #----------------------------------------
        
        label_list = Label(self, text="Marcações", bg='black', fg="white", font=("Arial", 14))
        label_list.place(x=self.size_w + 180, y=390)
    
        self.list_objs = Listbox(self, selectmode=SINGLE, exportselection=False, bg='black', fg="white",)
        
        scrolobj = Scrollbar(self.list_objs)
        scrolobj.config(command=self.list_objs.yview)
        scrolobj.pack(side="right", fill="y")
        self.list_objs.config(yscrollcommand=scrolobj.set) 
        self.list_objs.place(x=self.size_w + 170, y=420, width=140, height=320)
        self.list_objs.bind('<<ListboxSelect>>', self.list_objs_event)
        
        #-------------------------------------------------------------
        
        self.img_atual = Label(self, text="Imagem Atual: {}".format(self.videos[0]), bg='black', fg="white", font=("Arial", 14))
        self.img_atual.place(x=300, y=20)
        
        self.progress = Label(self, text="Progresso: {:0.3f}%".format(float(0)), bg='black', fg="white", font=("Arial", 14))
        self.progress.place(x=300, y=50)
        
        total = Label(self, text="Total: {}".format(len(self.videos)), bg='black', fg="white", font=("Arial", 14))
        total.place(x=650, y=20)
        
        self.status = Label(self, text="Status: {}".format('Não Salvo'), bg='black', fg="white", font=("Arial", 14))
        self.status.place(x=600, y=50)
    
        #--------------------------------------------------
   
        self.lb_id_frame = Label(self, text="ID Frame: {}".format(self.id_frame), bg='black', fg="white", font=("Arial", 14))
        self.lb_id_frame.place(x=780, y=50)

        self.bt_play = Button(self, text='Play', bg='black', fg="white", command=self.run_video)
        self.bt_play.place(x=680, y=90, height=25)
        
        self.bt_stop = Button(self, text='Stop', bg='black', fg="white", command=self.stop_video)
        self.bt_stop.place(x=740, y=90, height=25)
        
        self.bt_backward = Button(self, text='<<', bg='black', fg="white", command=self.backward_video)
        self.bt_backward.place(x=800, y=90, height=25)
        
        self.bt_forward = Button(self, text='>>', bg='black', fg="white", command=self.forward_video)
        self.bt_forward.place(x=860, y=90, height=25)
        
        
        self.bt_save_video = Button(self, text='Save..', bg='black', fg="white", command=self.save_video)
        self.bt_save_video.place(x=920, y=90, height=25)
        #--------------------------------------------------
    
        #------------
        self.ent_duration = Entry(self, name="ent_duration", textvariable=StringVar(self, value=self.DURATION))
        self.ent_duration.place(x=480, y=90, width=60, height=25)
        
        self.bt_duration = Button(self, text="Set:{}".format(self.DURATION), bg='black', fg="white", command=self.duration_handler)
        self.bt_duration.place(x=550, y=90, width=90, height=25)
        #------------
        
        #####
        self.set_position_video_init()
        self.next_img()
        self.load_annotation(self.videos[self.id])
        
        # reload line
        self.create_line_curso()
        #--------------
    
    
    def duration_handler(self):
        self.DURATION = int(self.ent_duration.get())
        self.bt_duration.config(text="Set:{}".format(self.DURATION))
        # self.ent_duration.delete(0,END)
        # self.ent_duration.insert(0,self.DURATION)
        
        idx = self.list_objs.curselection()[0]
        
        self.objetos_coo[idx][-1] = self.DURATION
        self.objetos_re_draw[idx][-1] = self.DURATION
        
        
    def load_config(self):
        data = None
        try:
            with open('video_config.json') as data_file:    
                data = json.load(data_file)
        except Exception, e:
            print ("Erro load config.json! {}".format(e))
    
        return data
    
    def parse_index(self, data):
        new_class = dict()
        for i in data:
            new_class.update({int(i):data[i]})
        return new_class
    
    def create_line_curso(self):
        self.vertical_line = self.canvas.create_line(0, 0, 0, 0, width=2, dash=(8, 6), fill='#1CF0C3')
        self.horizontal_line = self.canvas.create_line(0, 0, 0, 0, width=2, dash=(8, 6), fill='#1CF0C3')
    
    def file_item_select(self, event):
        
        self.objetos_coo = []
        self.objetos_re_draw = []
        self.list_objs.delete(0, END)       
        self.status.config(text="Status: {}".format('Não Salvo'))
        
        if self.id == len(self.videos) - 1:
            size = self.salvar.find(self.videos[self.id]) + len(self.videos[self.id])                    
            self.salvar = self.salvar[:size] + " " + str(self.idImagGlobal) + self.salvar[size:]                  
            self.arquivo.write(self.salvar)
        
        size = self.salvar.find(self.videos[self.id]) + len(self.videos[self.id])                    
        self.salvar = self.salvar[:size] + " " + str(self.idImagGlobal) + self.salvar[size:]            

        self.salvar = self.salvar + "\r\n"
        self.idImagGlobal = self.idImag
        self.idImag = 0
        
        idx = self.list_files.curselection()[0]
        self.id = idx
        
        # add nova imagem
        self.set_position_video_init()

        #####
        self.load_annotation(self.videos[self.id])
        
        self.img_atual.config(text="Imagem Atual: {}".format(self.videos[self.id]))
        percent = float((float(self.id) * 100) / float(len(self.videos)))
        self.progress.config(text="Progresso: {:0.3f}%".format(percent))
    
    def set_position_video_init(self):
        self.start_video = False 
        
        self.update_video()
        self.id_frame = 0
        self.lb_id_frame.config(text="ID Frame: {}".format(self.id_frame))
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, self.id_frame)
        
        self.next_img()
        self.update_img()
        self.redraw_img()
    
    
    def update_duration(self, dur):
        self.DURATION = int(dur)
        self.bt_duration.config(text="Set:{}".format(self.DURATION))
        
        self.ent_duration.delete(0, END)
        self.ent_duration.insert(0, self.DURATION)
    
    def load_annotation(self, name_img):  
        try:       
            full_path_save = "{}{}.json".format(self.path_save_anotation, name_img[:-4])
            
            with open(full_path_save, 'r') as json_file:
                data = json.loads(json_file.read())
            
                for obj in data['Objects']:
                    
                    class_name = obj['Class']
                    frame_id = obj['FrameID']
                    duration = obj['Duration']
                    
                    self.update_duration(duration)
                    
                    # add new class becase not exists
                    select_class = filter(lambda (k, v): v == class_name, self.switch_class.items())
                    
                    if len(select_class) == 0:
                        new_id = self.switch_class.keys()[-1] + 1
                        
                        self.switch_class.update({new_id:class_name})
                        
                        self.listbox.insert(END, self.switch_class[new_id])
                    
                    x = int(obj['X'])
                    y = int(obj['Y'])
                    w = int(obj['W'])
                    h = int(obj['H'])
                    
                    x1 = x
                    y1 = y
                    x2 = x + w
                    y2 = y + h
                    
                    self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2            
                    
                    self.objetos_coo.append([class_name, frame_id, self.x1, self.y1, (self.x2 - self.x1), (self.y2 - self.y1), duration])
                    self.x1, self.y1, self.x2, self.y2 = self.dcon_x(self.x1), self.dcon_y(self.y1), self.dcon_x(self.x2), self.dcon_y(self.y2)
                    self.objetos_re_draw.append([class_name, frame_id, self.x1, self.y1, (self.x2 - self.x1), (self.y2 - self.y1), duration])
                            
                    self.list_objs.insert(END, class_name)
            #--------------------
            
                print 'Load:', data            
                self.classe_info()
                
                for i, _ in enumerate(self.objetos_coo):
                    self.list_objs.selection_clear(i)
                 
                id_end = len(self.objetos_coo) - 1  
                self.list_objs.select_set(id_end)
              
                self.redraw_img()
                self.recolor_img(id_end) 
                
                try:
                    # seleciona a classe passado o nome da mesma    
                    clas_name = self.objetos_coo[id_end][0]
                    self.select_class_name(clas_name)
                except Exception, e:
                    print e
                
        except Exception, e:
            print "No annotation for the image: ", name_img, e
            
            # reload line
            self.create_line_curso()
        
    def recolor_img(self, idx):
        # self.update_video()
        
        c, id_f, x1, y1, x2, y2, dur = self.objetos_re_draw[idx]
        self.update_duration(dur)
        self.classe, self.id_frame, self.x1, self.y1, self.x2, self.y2 = c, id_f, x1, y1, (x2 + x1), (y2 + y1)
        
        self.canvas.create_rectangle(self.x1 - 5, self.y1 - 15, self.x1 + 60, self.y1, fill="yellow", outline='yellow', width=2)
        self.text_class = self.canvas.create_text(self.x1 + 25, self.y1 - 10, font="Arial 10", text=("{}").format(self.classe))
        
        self.canvas.create_rectangle(self.x1, self.y1, self.x2, self.y2, fill="", outline='yellow', width=2, dash=(8, 6))
        
        b = 8    
        self.canvas.create_oval(self.x1 - b // 2, self.y1 - b // 2, self.x1 + b // 2, self.y1 + b // 2, fill="green", outline='green', width=2)
        self.rect = self.canvas.create_oval(self.x2 - b // 2, self.y2 - b // 2, self.x2 + b // 2, self.y2 + b // 2, fill="green", outline='green', width=2)
  
    def list_objs_event(self, event):
        self.redraw_img()
        idx = self.list_objs.curselection()[0]
        
        
        self.set_position_video_from_anno(idx)
        
        self.recolor_img(idx)
        
        # reload line
        self.create_line_curso()
        
        #------------------------------------
    
    
    def set_position_video_from_anno(self, idx):
        _, id_f, _, _, _, _, dur = self.objetos_re_draw[idx]
        
        self.update_duration(dur)
        
        self.start_video = False 
        
        self.update_video()
        self.id_frame = id_f
        self.lb_id_frame.config(text="ID Frame: {}".format(self.id_frame))
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, self.id_frame)
        
        self.next_img()
        self.update_img()
        self.redraw_img()
        
    def find_pos(self, key):
        for i, idx in enumerate(self.switch_class.keys()):
            if idx == key:
                return i
        return None
    
    def class_item_select(self, e):
        self.classe = self.listbox.get(self.listbox.curselection())        
        key = [key for key, value in self.switch_class.items() if value == self.classe][0]
        
        # self.canvas.itemconfig(self.text_class, text="{}".format(self.classe))

        idx = self.find_pos(key)                        
        for i, _ in enumerate(self.switch_class):
            self.listbox.selection_clear(i)
        
        self.listbox.select_set(idx)
        
        if len(self.objetos_coo) > 0:
            # print 'classe selecionada: ', self.switch_class[key]
            self.classe = self.switch_class[key]
            
            # muda o nome da classe do objeto dinamicamente
            self.canvas.itemconfig(self.text_class, text="{}".format(self.classe))
            
            list_select = self.list_objs.curselection()[0]
            
            # muda classe nas listas
            self.objetos_coo[list_select][0] = self.classe
            self.objetos_re_draw[list_select][0] = self.classe
            
            # update list box
            
            self.list_objs.delete(list_select)
            self.list_objs.insert(list_select, self.classe)
            self.list_objs.select_set(list_select)
            
    # converte resolucao
    def con_x(self, x1):
        # resolucao camera
        xRes1 = self.frame.shape[1]
        # resolucao local
        xRes2 = self.size_w
        0
        a = (xRes1 * x1)
        b = xRes2
        x2 = (a - (a % b)) / b
        
        # x2=(xRes2*x1)/xRes1
        
        return x2
    
    def con_y(self, y1):
        # resolucao camera
        yRes1 = self.frame.shape[0]
        # resolucao local
        yRes2 = self.size_h
        
        a = (yRes1 * y1)
        b = yRes2
        y2 = (a - (a % b)) / b
        
        # y2=(yRes2*y1)/yRes1
        
        return y2
    
    # desconverte resolucao
    def dcon_x(self, x1):
        # resolucao camera
        xRes2 = self.frame.shape[1]
        # resolucao local
        xRes1 = self.size_w
        
        a = (xRes1 * x1)
        b = xRes2
        x2 = (a - (a % b)) / b
        
        # x2=(xRes2*x1)/xRes1
        
        return x2
    
    def dcon_y(self, y1):
        # resolucao camera
        yRes2 = self.frame.shape[0]
        # resolucao local
        yRes1 = self.size_h
        
        a = (yRes1 * y1)
        b = yRes2
        y2 = (a - (a % b)) / b
        
        # y2=(yRes2*y1)/yRes1
        
        return y2
    
    def select_class_name(self, clas_name):
        
        id_select_class = filter(lambda (k, v): v == clas_name, self.switch_class.items())[0][0]
                
        idx = self.find_pos(id_select_class)    
        
        for i, _ in enumerate(self.switch_class):
            self.listbox.selection_clear(i)
         
        self.listbox.select_set(idx)
        
        # reload line
        self.create_line_curso()
    
    def key_press(self, e):
        
        k = str(e.char)
        
        # para as teclas de atalho n atrapalharem na hora de digitar o track
        
        # para as teclas de atalho n atrapalharem na hora de digitar o track
        is_focus = True if str(self.ent_duration.focus_get()).split('.')[-1] == 'ent_duration' else False
        if is_focus == False:
            # troca a classe do objecto
            for key in self.switch_class.keys():
                if k == str(key):
                    
                    idx = self.find_pos(key)    
                    
                    for i, _ in enumerate(self.switch_class):
                        self.listbox.selection_clear(i)
                    
                    self.listbox.select_set(idx)
                    
                    if len(self.objetos_coo) > 0:
                        # print 'classe selecionada: ', self.switch_class[key]
                        self.classe = self.switch_class[key]
                        
                        # muda o nome da classe do objeto dinamicamente
                        self.canvas.itemconfig(self.text_class, text="{}".format(self.classe))
                        
                        list_select = self.list_objs.curselection()[0]
                        
                        # muda classe nas listas
                        self.objetos_coo[list_select][0] = self.classe
                        self.objetos_re_draw[list_select][0] = self.classe
                        
                        # update list box
                        
                        self.list_objs.delete(list_select)
                        self.list_objs.insert(list_select, self.classe)
                        self.list_objs.select_set(list_select)
                        
                    
        # del 127
        if k == str('c'):
            print "Itens:", len(self.canvas.find_all())
            self.canvas.delete("all")
            
            if len(self.objetos_coo) > 0:
                idx = self.list_objs.curselection()[0]
                
                self.list_objs.delete(idx)
             
                self.objetos_coo.pop(idx)
                self.objetos_re_draw.pop(idx)
                
                self.redraw_img()
            
                self.list_objs.select_set(len(self.objetos_coo) - 1)
              
                id_end = len(self.objetos_coo) - 1
                self.list_objs.select_set(id_end)
               
                try:
                    # seleciona a classe passado o nome da mesma    
                    clas_name = self.objetos_coo[id_end][0]
                    self.select_class_name(clas_name)
                    self.recolor_img(id_end) 
                except Exception, e:
                    print e
                
                # reload line
                self.create_line_curso()
        
        # grava o objeto
        if k == str('w'):
            print "Itens:", len(self.canvas.find_all())
            self.canvas.delete("all")
            
            h, w, _ = self.frame.shape
            
            
            print self.DURATION
            print 'Anotação gerada!'
            print 'Nome imagem:', self.videos[self.id]
            print 'Resolução: ' , (w, h) 
            print 'Objetos: ', self.objetos_coo
            print '-----------------------------------------------------'
            
            string = self.videos[self.id]
            special = np.array([True if (s.isalnum() or s == "_" or s == "-" or s == ":" \
                          or s == ":" or s == "." or s == "(" or s == ")") else False for s in string])
            
            if len(np.where(special == False)[0]) > 0:
                
                self.videos[self.id] = "".join(s for s in string if s.isalnum() or s == "_" or s == "-" or s == ":" \
                                             or s == ":" or s == "." or s == "(" or s == ")")
            
                os.rename(self.path_input + string, self.path_input + self.videos[self.id])
                
                self.save_file_json(self.path_save_anotation, self.videos[self.id], w, h, self.objetos_coo)
            
            else:
                self.save_file_json(self.path_save_anotation, self.videos[self.id], w, h, self.objetos_coo)
            
            try:
                shutil.copy2(self.path_input + self.videos[self.id], self.path_save_img)
            except Exception, e:
                print 'Image already exists! ', e
            
            self.objetos_coo = []
            self.objetos_re_draw = []
            self.list_objs.delete(0, END) 
            
            self.classe_info()
            
            self.status.config(text="Status: {}".format('Salvo'))
            
            # add nova imagem
            self.update_video()
            
            # reload line
            self.create_line_curso()
        
        # avanca image
        if k == str('d'): 
            self.start_video = False 
            print "Itens:", len(self.canvas.find_all())
            self.canvas.delete("all")
        
            if self.id < len(self.videos) - 1:
                
                self.objetos_coo = []
                self.objetos_re_draw = []
                self.list_objs.delete(0, END)      
                self.status.config(text="Status: {}".format('Não Salvo'))
                
                if self.id == len(self.videos) - 1:
                    size = self.salvar.find(self.videos[self.id]) + len(self.videos[self.id])                    
                    self.salvar = self.salvar[:size] + " " + str(self.idImagGlobal) + self.salvar[size:]                  
                    self.arquivo.write(self.salvar)
                
                size = self.salvar.find(self.videos[self.id]) + len(self.videos[self.id])                    
                self.salvar = self.salvar[:size] + " " + str(self.idImagGlobal) + self.salvar[size:]            
    
                self.salvar = self.salvar + "\r\n"
                self.idImagGlobal = self.idImag
                self.idImag = 0
                self.id = self.id + 1
                
                # add nova imagem
                self.update_video()
        
                #####
                self.load_annotation(self.videos[self.id])
                
                for i, _ in enumerate(self.videos):
                    self.list_files.selection_clear(i)
                self.list_files.select_set(self.id)
                
                # reload line
                self.create_line_curso()
        
        # volta image
        if k == str('a'):
            self.start_video = False
            print "Itens:", len(self.canvas.find_all())
            self.canvas.delete("all")
            
            if self.id > 0:
            
                self.objetos_coo = []
                self.objetos_re_draw = []
                self.list_objs.delete(0, END) 
                self.status.config(text="Status: {}".format('Não Salvo'))
                
                if self.id == len(self.videos) - 1:
                    size = self.salvar.find(self.videos[self.id]) + len(self.videos[self.id])                    
                    self.salvar = self.salvar[:size] + " " + str(self.idImagGlobal) + self.salvar[size:]                  
                    self.arquivo.write(self.salvar)
                
                size = self.salvar.find(self.videos[self.id]) + len(self.videos[self.id])                    
                self.salvar = self.salvar[:size] + " " + str(self.idImagGlobal) + self.salvar[size:]            
    
                self.salvar = self.salvar + "\r\n"
                self.idImagGlobal = self.idImag
                self.idImag = 0
                self.id = self.id - 1
            
                # add nova imagem
                self.update_video()
        
                #####
                self.load_annotation(self.videos[self.id])
                
                for i, _ in enumerate(self.videos):
                    self.list_files.selection_clear(i)
                self.list_files.select_set(self.id)
            
                # reload line
                self.create_line_curso()
        
        self.img_atual.config(text="Imagem Atual: {}".format(self.videos[self.id]))
        percent = float((float(self.id) * 100) / float(len(self.videos)))
        self.progress.config(text="Progresso: {:0.3f}%".format(percent))
        
        if k == str('i'):
            print 'Informacoes:'
            print 'Objs:', self.objetos_coo
            print 'Draw: ', self.objetos_re_draw
            print 'Classes: ', self.switch_class
    
    def update_video(self):
        
        full_path_video = "{}{}".format(self.path_input, self.videos[self.id])
        self.capture = cv2.VideoCapture(full_path_video)
        
        self.next_img()
        self.update_img()
    
    
    def update_img(self):
        frame_res = cv2.resize(self.frame.copy(), (self.size_w, self.size_h))
        im = cv2.cvtColor(frame_res, cv2.COLOR_BGR2RGB)
        a = PIL.Image.fromarray(im)
        self.tk_im = ImageTk.PhotoImage(image=a)
        
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_im)
    
    def next_img(self):
        _, self.frame = self.capture.read()
        
    def run_video(self):
        if self.start_video == False:
            self.start_video = True
            threading.Thread(target=self.thread_run_video).start()
        
    def thread_run_video(self):
        while self.start_video:
            get_id = self.capture.get(cv2.CAP_PROP_POS_FRAMES) - 2
            self.id_frame = int(get_id)
            self.lb_id_frame.config(text="ID Frame: {}".format(self.id_frame))
            self.next_img()
            self.update_img()
            cv2.waitKey(30)
    
    def stop_video(self):
        self.start_video = False
    
    def forward_video(self):
        self.stop_video()
        get_id = self.capture.get(cv2.CAP_PROP_POS_FRAMES)
        self.id_frame = int(get_id)
        self.lb_id_frame.config(text="ID Frame: {}".format(self.id_frame))
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, self.id_frame)
        
        self.next_img()
        self.update_img()
    
    def backward_video(self):
        self.stop_video()
        get_id = self.capture.get(cv2.CAP_PROP_POS_FRAMES) - 2
        self.id_frame = int(get_id)
        self.lb_id_frame.config(text="ID Frame: {}".format(self.id_frame))
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, self.id_frame)
        
        self.next_img()
        self.update_img()
    
    def save_video(self):
        threading.Thread(target=self.thread_save_video).start()
        
    def thread_save_video(self):
        full_path_video = "{}{}".format(self.path_input, self.videos[self.id])
        
        print full_path_video
        cap = cv2.VideoCapture(full_path_video)
        print self.id_frame - 1
        cap.set(cv2.CAP_PROP_POS_FRAMES, self.id_frame - 1)
        
        _, frame = cap.read()
        H, W, _ = frame.shape
        fourcc = cv2.VideoWriter_fourcc(*'x264')
        out = cv2.VideoWriter('/home/avantia/python-workspace/PoseTensorRTActionDetection/EverydayActionsDataset/fall/vid_{:06d}.avi'.format(self.id_frame), fourcc, 25.0, (W, H))
        
        count = 0
        while count < self.DURATION * 4:
            _, frame = cap.read()
            out.write(frame) 
            
            cv2.waitKey(150)
            count += 1
        
        cap.release()
        out.release()
        
        print "Gravação finalizada!"
    
        
        
    def on_button_press(self, event):
        self.redraw_img()
        
        # save mouse drag start position
        self.start_x, self.start_y = (event.x, event.y)
        self.x1, self.y1 = (event.x, event.y)
        
        if self.dist1 < self.TDIST or self.dist2 < self.TDIST:
            
            pass
            
        else:    
            self.canvas.create_rectangle(self.x1 - 5, self.y1 - 15, self.x1 + 60, self.y1, fill="green", outline='green', width=2)
            self.text_class = self.canvas.create_text(self.x1 + 25, self.y1 - 10, font="Arial 10", text=("{}").format(self.classe))
            self.rect = self.canvas.create_rectangle(self.x1, self.y1, 1, 1, fill="", outline='green', width=2, dash=(8, 6))
            
        self.status.config(text="Status: {}".format('Não Salvo'))

    def on_move_press(self, event):
        curX, curY = (event.x, event.y)
              
        if self.dist1 < self.TDIST:
            self.x1, self.y1 = curX, curY
        else:
            self.x2, self.y2 = curX, curY

        # expand rectangle as you drag the mouse
        # --
        try:
            self.canvas.coords(self.rect, self.x1, self.y1, self.x2, self.y2)
        except Exception, e:
            print e    
        # --
        
        if self.dist1 < self.TDIST:
             
            list_select = self.list_objs.curselection()[0]
             
            self.objetos_re_draw[list_select][2] = self.x1
            self.objetos_re_draw[list_select][3] = self.y1
             
            self.objetos_coo[list_select][2] = self.x1
            self.objetos_coo[list_select][3] = self.y1
             
            self.canvas.coords(self.rect, self.x1, self.y1, self.objetos_re_draw[list_select][2] + self.objetos_re_draw[list_select][4], \
                               self.objetos_re_draw[list_select][3] + self.objetos_re_draw[list_select][5])
            
        elif self.dist2 < self.TDIST:
             
            list_select = self.list_objs.curselection()[0]
             
            self.objetos_re_draw[list_select][4] = self.x2 - self.objetos_re_draw[list_select][2]
            self.objetos_re_draw[list_select][5] = self.y2 - self.objetos_re_draw[list_select][3]
             
            self.objetos_coo[list_select][4] = self.x2 - self.objetos_coo[list_select][2]
            self.objetos_coo[list_select][5] = self.y2 - self.objetos_coo[list_select][3]
             
            self.canvas.coords(self.rect, self.objetos_re_draw[list_select][2], self.objetos_re_draw[list_select][3], self.x2, self.y2)
        
    def on_move(self, event):
        
        curX, curY = (event.x, event.y)
              
        self.canvas.coords(self.vertical_line, curX, 0, curX, self.size_h)
        self.canvas.coords(self.horizontal_line, 0, curY, self.size_w, curY)
        
        list_select = self.list_objs.curselection()[0]
        
        self.dist1 = np.linalg.norm(np.array([curX, curY]) - \
                              np.array([self.objetos_re_draw[list_select][2], self.objetos_re_draw[list_select][3]]))
        
        self.dist2 = np.linalg.norm(np.array([curX, curY]) - \
                              np.array([self.objetos_re_draw[list_select][2] + self.objetos_re_draw[list_select][4],
                                        self.objetos_re_draw[list_select][3] + self.objetos_re_draw[list_select][5]]))
        
        b = 8 
        if self.dist1 < self.TDIST:
            self.canvas.create_oval(self.x1 - b // 2, self.y1 - b // 2, self.x1 + b // 2, self.y1 + b // 2, fill="white", outline='white', width=2)
        else:
            self.canvas.create_oval(self.x1 - b // 2, self.y1 - b // 2, self.x1 + b // 2, self.y1 + b // 2, fill="green", outline='green', width=2)
        
        if self.dist2 < self.TDIST:
            self.canvas.create_oval(self.x2 - b // 2, self.y2 - b // 2, self.x2 + b // 2, self.y2 + b // 2, fill="white", outline='white', width=2)
        else:
            self.canvas.create_oval(self.x2 - b // 2, self.y2 - b // 2, self.x2 + b // 2, self.y2 + b // 2, fill="green", outline='green', width=2)
        
    def on_button_release(self, event):
        
        get_id = self.capture.get(cv2.CAP_PROP_POS_FRAMES)
        self.id_frame = int(get_id)
        
        print "Itens:", len(self.canvas.find_all())
        self.canvas.delete("all")
        
        if self.idImag == 0:
            self.salvar = self.salvar + "pos_cap/" + self.videos[self.id]
        
#         if self.dist1 < self.TDIST or self.dist2 > self.TDIST:
#         
#             if self.y2 < self.y1:
#                 aux = self.y2
#                 self.y2 = self.y1
#                 self.y1 = aux
#             
#             if self.x2 < self.x1:
#                 aux = self.x2
#                 self.x2 = self.x1
#                 self.x1 = aux
#             
        
        if self.dist1 < self.TDIST or self.dist2 < self.TDIST:
            list_select = self.list_objs.curselection()[0]
        else:
            self.objetos_re_draw.append([self.classe, self.id_frame, self.x1, self.y1, (self.x2 - self.x1), (self.y2 - self.y1), self.DURATION])
       
        self.x1, self.y1, self.x2, self.y2 = self.con_x(self.x1), self.con_y(self.y1), self.con_x(self.x2), self.con_y(self.y2)
                                         
        self.salvar = self.salvar + " " + str(self.x1) + " " + str(self.y1) + " " + str(self.x2 - self.x1) + " " + str(self.y2 - self.y1)
        # roi = self.frame[self.y1 + 1:self.y2 - 1, self.x1 + 1:self.x2 - 1]        
        self.idImag = self.idImag + 1
        self.idImagGlobal = self.idImag
     
        if self.dist1 < self.TDIST:
            self.objetos_coo[list_select][2] = self.x1 
            self.objetos_coo[list_select][3] = self.y1
        
        elif self.dist2 < self.TDIST:
            self.objetos_coo[list_select][4] = self.x2 - self.objetos_coo[list_select][2]
            self.objetos_coo[list_select][5] = self.y2 - self.objetos_coo[list_select][3]
        
        else:
            self.objetos_coo.append([self.classe, self.id_frame, self.x1, self.y1, (self.x2 - self.x1), (self.y2 - self.y1), self.DURATION])
            self.list_objs.insert(END, self.classe)
        
        print "Classe: " + str(self.classe) + " | Nome: " + str(self.videos[self.id])[:-4] + "_" + str(self.idImagGlobal) + " | Coordenadas: " + str(self.x1) + ", " + str(self.y1) + ", " + str(self.x2) + ", " + str(self.y2)
        self.classe_info()
        
        if self.dist1 < self.TDIST or self.dist2 < self.TDIST:
            id_end = list_select
        else:
            for i, _ in enumerate(self.objetos_coo):
                self.list_objs.selection_clear(i)
    
            id_end = len(self.objetos_coo) - 1
        
        self.list_objs.select_set(id_end)
            
        self.redraw_img()
        self.recolor_img(id_end) 
        
        # reload line
        self.create_line_curso()
        
    def redraw_img(self):
        self.update_img()
        
        for c, id_f, x1, y1, x2, y2, dur  in self.objetos_re_draw:
            self.update_duration(dur)
            self.classe, self.id_frame, self.x1, self.y1, self.x2, self.y2 = c, id_f, x1, y1, (x2 + x1), (y2 + y1)
            
            self.canvas.create_rectangle(self.x1 - 5, self.y1 - 15, self.x1 + 60, self.y1, fill="green", outline='green', width=2)
            self.text_class = self.canvas.create_text(self.x1 + 25, self.y1 - 10, font="Arial 10", text=("{}").format(self.classe))
            self.rect = self.canvas.create_rectangle(self.x1, self.y1, self.x2, self.y2, fill="", outline='green', width=2, dash=(8, 6))
    
    def classe_info(self):
        print '----------------------------------------------'
        print 'Selecione a classe de objeto:'
        print self.switch_class
        print '----------------------------------------------'
    
    def save_file_json(self, path_save, name_img, res_wid, res_hei, objetos_coo):
                
        list_objects = []
        for obj in objetos_coo:
            (type_class, frame_id, x, y, w, h, dur) = obj
            objetc = {
                "FrameID":frame_id,
                "Duration":dur,
                "Class":type_class,
                "X":x,
                "Y":y,
                "W":w,
                "H":h
            }
            list_objects.append(objetc)    
        
        
        full_path_save = "{}{}.json".format(path_save, name_img[:-4])
        Json_annotation = {
            "Dataset":"EverydayActionsDataset",
            "Owner":"Mouglas",
            "FileName":name_img,
            "Width":res_wid,
            "Height":res_hei,
            "Depth":3,
            "Objects":list_objects
        }
        
        with open(full_path_save, 'w') as json_file:
            json.dump(Json_annotation, json_file, indent=4)
            
        print("Anotation of the {} save!".format(name_img))
    #==========================================================================================


if __name__ == "__main__":
#     root = Tk()
#     app = TKMarkCoorAnnotation(root)
#     root.mainloop()
#     
    
    app = TKMarkCoorAnnotation()
    global SIZE_W, SIZE_H
    app.master.geometry("{}x{}".format(SIZE_W + 320, SIZE_H + 156))
    app.master.title("Marcador de Anotações em Vídeos")
    
    app.pack(expand=YES, fill=BOTH)
    app.mainloop()
