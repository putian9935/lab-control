from tkinter import *
import time
from tkinter import messagebox
import asyncio 

import numpy as np
import glob
import os

from .EMCCD_simControl import action_changeFilenameAndStartCamAcq, action_StopCamAcq


class MyTk(Tk):
    def __init__(self):
        super().__init__()
        self.task = [
            asyncio.create_task(self.aupdate()),
        ]
        self.spooling = IntVar(self)
        self.job = None

    async def aupdate(self):
        """ the Tk loop """
        while True:
            self.update()
            try:
                await asyncio.sleep(0.01)
            except:
                return

    def close(self):
        if self.job:
            self.job.cancel()
        for t in self.task:
            if not t.cancelled() and not t.done():
                t.cancel()
        self.destroy()

exported_funcs= {}
def create():
    global exported_funcs 
    param_list = []
    param_num_list = []
    # param_list = ['MOTpower', 'MOT-detuning', 'CoilCurrent', 'EMgain', 'Exposuretime', 'Seq'\
                # ,'TOF(B off)', 'Bx', 'By', 'Bz','CoolMOT-duration','CoolMOT-detuning','CoolMOT-detuning-ramp-time']
    # param_num_list = ['300mV', '-40MHz', '36A', '2', '3ms', 'CoolMOTv10', '2.5-0.5-6', '-250mA', '-100mA', '220mA','3.5ms','-140MHz','1.5ms']

    def initializeVar():
        global count, index, timestamp, index_list, param_box_list1, param_box_list2,fn
        index = 0
        count = 0
        timestamp = str(round(time.time()))
        index_list = []
        param_box_list1 = []
        param_box_list2 = []
        update_ind()
        update_tstp()   
        B_load.config(state = 'normal')

    def update_tstp():
        ent_tstp.config(state = 'normal')
        ent_tstp.delete(0,END)
        ent_tstp.insert(0,timestamp)
        ent_tstp.config(state = 'readonly')

    def update_ind():
        ent_ind.config(state = 'normal')
        ent_ind.delete(0,END)
        ent_ind.insert(0,str(count))
        ent_ind.config(state = 'readonly')    
        
    def next_data():
        global count, timestamp
        count += 1
        timestamp = str(round(time.time()))
        update_ind()
        update_tstp()   
        B_next.config(state = 'disabled')
        B_gen.config(state = 'normal')
    def gene_data() -> str:
        global fn, des_name, fn_list,index
        sp = '_'
        today = time.ctime()
        today_list = today.split()
        des_name = today_list[1] + sp + today_list[2] + sp + today_list[-1] + sp + 'data description' + '.txt'
        global param_box_list1,param_box_list2
        fn_list = []
        
        fn = str(count) + sp + timestamp + sp
        fn_list = ['index'] + ['timestamp'] + ['description']
        if ent_des.get() != '':
            fn += ent_des.get() + sp
        else:
            fn += 'NA' + sp

        para_num= len(param_box_list2)
        if para_num != 0:
            if param_box_list2[-1].get() == '':
                para_num -= 1
            
            if para_num != 0:
                for i in range(para_num):
                    fn += param_box_list2[i].get() + sp
                    fn_list += [param_box_list1[i].get()]

        ent_output.config(state = 'normal')
        ent_output.delete(0,END)
        ent_output.insert(0,fn)
        ent_output.config(state = 'readonly') 
        
        root.clipboard_clear()
        root.clipboard_append(fn)
        root.update()

        B_gen.config(state = 'disabled')
        B_next.config(state = 'normal')
        B_disc.config(state = 'normal')
        # print(fn_list)
        # print(fn.split('_'))
        f = open(des_name, 'ab')
        np.savetxt(f, [fn_list],fmt="%s")
        np.savetxt(f, [fn.split('_')[:-1]],fmt="%s")
        f.close()
        return fn

    def add_para():
        global index,len_given_param,param_box_list1,param_box_list2
        len_given_param = len(param_list)
        box_n = len(param_box_list1)
        index = box_n+1
        if box_n >= 1:
            if param_box_list1[-1].get()=='' or param_box_list2[-1].get()=='':
                messagebox.showinfo('Error', 'Empty paramater name or value')
                return 0
        para_index = Entry(frame_para,)
        para_index.grid(row = box_n+2,column = 0, padx = 5,pady = 5) 
        para_index.insert(0,index)
        para_index.config(state = 'disable')
        param_box_list1 += [Entry(frame_para,)]
        param_box_list1[-1].grid(row = box_n+2,column = 1, padx = 5,pady = 5) 
        param_box_list2 += [Entry(frame_para,)]
        param_box_list2[-1].grid(row = box_n+2,column = 2, padx = 5,pady = 5)
        if box_n< len_given_param:
            param_box_list1[-1].insert(0,param_list[box_n])
            param_box_list2[-1].insert(0,param_num_list[box_n])
            
    def dis_data():
        global des_name
        suffix = '.fits'
        data_fns = glob.glob('*.fits')
        if fn+suffix in data_fns:
            os.rename(fn+suffix, fn+'discard'+suffix)
            B_disc.config(state = 'disabled')
            with open(des_name,'r+') as des_fl:
                lines = des_fl.readlines()
                des_fl.seek(0)
                des_fl.truncate()
                des_fl.writelines(lines[:-2])
            f = open(des_name, 'ab')
            np.savetxt(f, [fn_list+['discard']],fmt="%s")
            np.savetxt(f, [fn.split('_')[:-1]+['discard']],fmt="%s")
            f.close()
        else:
            messagebox.showinfo('Error', 'No such file found')
    def load_description():
        for i in range(len(param_list)):
            add_para()
        B_load.config(state = 'disabled')

    def cam_set_filename_and_start_acq():
    #     print(event)
        print('setting camera filename')
        try:
            cam_filename = fn
            print(cam_filename)
        except:
            cam_filename = 'exp00'
        action_changeFilenameAndStartCamAcq( filename=cam_filename)

    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            root.close()   

    exported_funcs['load'] = load_description
    exported_funcs['next'] = next_data
    exported_funcs['gene'] = gene_data
    exported_funcs['set_cam'] = cam_set_filename_and_start_acq


    root = MyTk()
    root.title('Data File Name manager v0.1')
    root.grid_rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    # default_font = tkFont.nametofont("TkDefaultFont")
    # default_font.configure(size=15)

    frame_main = Frame(root)
    frame_main.grid(sticky='news')

    label1 = Label(frame_main, text="Data File Name manager v0.1")
    label1.grid(row=0, column=0, pady=(5, 0), sticky='nw')

    frame_func = LabelFrame(frame_main, text = 'Functions:',padx = 5, pady = 5)
    frame_func.grid(row=1, column=0,padx = 5,pady = 5, sticky='nw')

    B_next = Button(frame_func, text = 'Next',command = next_data)
    B_next.grid(row = 0,column = 0, padx = 10,pady = 5)
    B_gen = Button(frame_func, text = 'Generate',command = gene_data)
    B_gen.grid(row = 0,column = 1, padx = 10,pady = 5)
    B_disc = Button(frame_func, text = 'Discard',command = dis_data)
    B_disc.grid(row = 0,column = 2, padx = 10,pady = 5)
    B_disc.config(state = 'disabled')
    B_load = Button(frame_func, text = 'Load',command = load_description)
    B_load.grid(row = 0,column = 3, padx = 10,pady = 5)

    B_camFnAcq = Button(frame_func, text = 'cam fn&Acq',command = cam_set_filename_and_start_acq)
    # B_camFnAcq = Button(frame_func, text = 'cam fn&Acq')
    B_camFnAcq.grid(row = 0,column = 5, padx = 10,pady = 5)
    ##########################################################################################
    frame_basc = LabelFrame(frame_main, text = 'Basic Info:',padx = 5, pady = 5)
    frame_basc.grid(row=2, column=0,padx = 5,pady = 5, sticky='nw')

    label_ind = Label(frame_basc, text="Data Index:")
    label_ind.grid(row=0, column=0, pady=(5, 0), sticky='nw')
    ent_ind = Entry(frame_basc,)
    ent_ind.grid(row=0, column=1, padx = 10, pady = 5, sticky='nw')

    label_tstp = Label(frame_basc, text="Timestamp:")
    label_tstp.grid(row=1, column=0, pady=(5, 0), sticky='nw')
    ent_tstp = Entry(frame_basc,)
    ent_tstp.grid(row=1, column=1, padx = 10, pady = 5, sticky='nw')
    # ent_tstp.config(state = 'readonly')

    label_des = Label(frame_basc, text="Description:")
    label_des.grid(row=2, column=0, pady=(5, 0), sticky='nw')
    ent_des = Entry(frame_basc,)
    ent_des.grid(row=2, column=1, padx = 10, pady = 5, sticky='nw')
    #############PARAMETER_FRAME#############################################
    frame_para = LabelFrame(frame_main, text = 'Experiment Parameters:',padx = 5, pady = 5)
    frame_para.grid(row=3, column=0,padx = 5,pady = 5, sticky='nw')

    B_add_para = Button(frame_para, text = ' + ',command = add_para)
    B_add_para.grid(row = 0,column = 0, padx = 5,pady = 5)
    label_add_para = Label(frame_para, text="<--- Add parameter")
    label_add_para.grid(row=0, column=1,padx = 5,pady = 5, sticky='nw')
    label_index = Label(frame_para, text="Index")
    label_index.grid(row=1, column=0,padx = 5,pady = 5, sticky='nw')
    label_index.config(state = 'disabled')
    label_paraname = Label(frame_para, text="Parameter Name")
    label_paraname.grid(row=1, column=1,padx = 5,pady = 5, sticky='nw')
    label_paraval = Label(frame_para, text="Parameter Value")
    label_paraval.grid(row=1, column=2,padx = 5,pady = 5, sticky='nw')
    initializeVar()
    #############OUTPUT######################################################
    frame_output = LabelFrame(frame_main, text = 'Output:',padx = 5, pady = 5)
    frame_output.grid(row=4, column=0,padx = 5,pady = 5, sticky='nw')
    ent_output = Entry(frame_output,width = 50)
    ent_output.grid(row=0, column=0, padx = 10, pady = 5, sticky='nw')

    root.protocol("WM_DELETE_WINDOW", lambda : print('Please close from the terminal!'))
    return root 

def get_new_name():
    ret = exported_funcs['gene']()
    exported_funcs['next']()
    return ret 

async def main():
    win = create()
    exported_funcs['load']()
    await win.task[0]

if __name__ == '__main__':
    asyncio.run(main())