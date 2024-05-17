# main.py
import socket
import json
import requests
import sys
import os
import threading
from tkinter import Tk, Label, Button, Entry, StringVar, ttk, messagebox
from tqdm import tqdm\

PROGRESS = {}
TASKS = []
WORKERS = []

class WorkerGUI:
    def __init__(self, master, num_parts=2):
        self.master = master
        master.title("Worker Status")

        master.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.status_var = StringVar()
        self.status_var.set("Waiting for tasks...")
        
        self.status_label = Label(master, textvariable=self.status_var)
        self.status_label.pack(pady=10)

        
        self.part_progress = ttk.Progressbar(master, orient="horizontal", length=300, mode="determinate")
        self.part_progress.pack(pady=5)

    # if worker window is closed, unregister worker
    def on_closing(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((COORDINATOR_IP, 5002))
            s.sendall(b'WORKER_UNREGISTER')
            response = s.recv(1024).decode()
            if response == 'UNREGISTERED':
                print('Worker unregistered from coordinator.')
            else:
                print('Error unregistering worker from coordinator.')
            s.close()
        self.master.destroy()
    def update_status(self, message):
        self.status_var.set(message)

    def update_progress(self, value, part_num):
        self.part_progress['value'] = max(value, self.part_progress['value'])
        
def download_part(url, start, end, part_num, gui):
    headers = {'Range': f'bytes={start}-{end}'}
    response = requests.get(url, headers=headers, stream=True)
    file_name = f'parts/part_{part_num}'
    if not os.path.exists('parts'):
        os.makedirs('parts')
    total_size = end - start + 1
    with open(file_name, 'wb') as file, tqdm(
        total=total_size, unit='B', unit_scale=True, desc=f'Part {part_num}', ncols=100
    ) as pbar:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)
                pbar.update(len(chunk))
                gui.update_progress(file.tell() / total_size * 100, part_num)

    gui.update_status(f'Part {part_num} downloaded.')
    send_part_to_coordinator(file_name, part_num, gui)

def send_part_to_coordinator(file_name, part_num, gui):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((COORDINATOR_IP, 5001 + part_num))
        with open(file_name, 'rb') as file:
            while chunk := file.read(1024):
                s.sendall(chunk)
        s.shutdown(socket.SHUT_WR)
    os.remove(file_name)
    gui.update_status(f'Part {part_num} sent to coordinator.')

def handle_task(task, gui):
    download_part(task['url'], task['start'], task['end'], task['part_num'], gui)

def start_worker_server(host, port, gui):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    # get my ip
    my_ip = socket.gethostbyname(socket.gethostname())
    gui.update_status(f'Worker listening on {my_ip}:{port}')

    while True:
        client_sock, _ = server.accept()
        request = client_sock.recv(1024).decode()
        task = json.loads(request)
        client_sock.sendall(b'ACK')
        client_sock.close()
        gui.update_status(f'Received task for part {task["part_num"]}')
        threading.Thread(target=handle_task, args=(task, gui)).start()

class CoordinatorGUI:
    def __init__(self, master):

        my_ip = socket.gethostbyname(socket.gethostname())

        self.master = master
        master.title("Coordinator Status")

        self.label = Label(master, text="Coordinator IP:" + my_ip)
        self.label.pack(pady=5)
        
        self.url_label = Label(master, text="File URL:")
        self.url_label.pack(pady=5)
        
        self.url_entry = Entry(master, width=50)
        self.url_entry.pack(pady=5)
        
        self.start_button = Button(master, text="Start Download", command=self.start_download)
        self.start_button.pack(pady=10)
        
        self.status_var = StringVar()
        self.status_var.set("Enter URL and start download...")
        
        self.status_label = Label(master, textvariable=self.status_var)
        self.status_label.pack(pady=10)
        
        self.progress = ttk.Progressbar(master, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=10)

    def update_status(self, message):
        self.status_var.set(message)

    def update_progress(self, value):
        self.progress['value'] = value

    def start_download(self):
        url = self.url_entry.get()
        if url:
            threading.Thread(target=start_distributed_download, args=(url, url.split('/')[-1].replace('%20', ' '), 1, WORKERS, self)).start()
        else:
            self.update_status("Please enter a valid URL.")

def get_file_size(url):
    response = requests.head(url, allow_redirects=True)
    return int(response.headers.get('content-length', 0))

def receive_part(part_num, gui):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 5001 + part_num))
        s.listen(1)
        conn, addr = s.accept()
        with open(f'part_{part_num}', 'wb') as file:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                file.write(data)
        conn.close()
    gui.update_status(f'Part {part_num} received.')
    gui.update_progress((part_num + 1) * 100 / NUM_PARTS)

def combine_parts(output_file, num_parts, gui):
    with open(output_file, 'wb') as final_file:
        for i in range(num_parts):
            with open(f'part_{i}', 'rb') as part_file:
                final_file.write(part_file.read())
            os.remove(f'part_{i}')
    gui.update_status('File combined successfully.')

def start_distributed_download(url, output_file, num_parts, workers, gui):
    gui.update_status("Starting download...")
    file_size = get_file_size(url)
    part_size = file_size // num_parts

    threads = []
    for i in range(num_parts):
        start = i * part_size
        end = start + part_size - 1 if i < num_parts - 1 else file_size - 1
        worker = workers[i % len(workers)]
        thread = threading.Thread(target=send_task_to_worker, args=(worker, url, start, end, i, gui))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    receive_threads = []
    for i in range(num_parts):
        receive_thread = threading.Thread(target=receive_part, args=(i, gui))
        receive_threads.append(receive_thread)
        receive_thread.start()

    for thread in receive_threads:
        thread.join()

    combine_parts(output_file, num_parts, gui)

def send_task_to_worker(worker, url, start, end, part_num, gui):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((worker['ip'], worker['port']))
        task = {
            'url': url,
            'start': start,
            'end': end,
            'part_num': part_num
        }
        s.sendall(json.dumps(task).encode())
        s.recv(1024)  # Wait for acknowledgment
    gui.update_status(f'Sent task for part {part_num} to worker {worker["ip"]}')

class RoleSelectorGUI:
    def __init__(self, master):
        self.master = master
        master.title("Select Role")
        
        self.label = Label(master, text="Select Role:")
        self.label.pack(pady=10)
        
        self.worker_button = Button(master, text="Worker", command=self.worker)
        self.worker_button.pack(pady=5)
        
        self.coordinator_button = Button(master, text="Coordinator", command=self.coordinator)
        self.coordinator_button.pack(pady=5)

    def worker(self):
        self.master.destroy()
        coordinator_ip = self.get_coordinator_ip()
        if coordinator_ip:
            start_worker(coordinator_ip)

    def coordinator(self):
        self.master.destroy()
        start_coordinator()

    def get_coordinator_ip(self):
        coordinator_ip = StringVar(self.master)
    
        def on_submit():
            nonlocal coordinator_ip
            ip = ip_entry.get()
            if ip:
                coordinator_ip.set(ip)
                # tell coordinator that worker is ready
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip, 5002))
                    s.sendall(b'WORKER_REGISTER')
                    response = s.recv(1024).decode()
                    if response == 'REGISTERED':
                        print('Worker registered with coordinator.')
                    else:
                        print('Error registering worker with coordinator.')

                    s.close()

                ip_window.destroy()
            else:
                messagebox.showerror("Error", "Please enter a valid IP address")
        
        ip_window = Tk()
        ip_window.title("Enter Coordinator IP")
        
        label = Label(ip_window, text="Coordinator IP:")
        label.pack(pady=5)
        
        ip_entry = Entry(ip_window)
        ip_entry.pack(pady=5)
        
        submit_button = Button(ip_window, text="Submit", command=on_submit)
        submit_button.pack(pady=10)
        
        ip_window.mainloop()
        return coordinator_ip.get()


def show_workers():
    print('Workers:')
    for worker in WORKERS:
        print(worker['ip'])    

def start_worker(coordinator_ip):
    global COORDINATOR_IP
    global NUM_PARTS

    COORDINATOR_IP = coordinator_ip
    HOST = '0.0.0.0'
    PORT = 5000
    
    root = Tk()
    gui = WorkerGUI(root, NUM_PARTS)
    
    threading.Thread(target=start_worker_server, args=(HOST, PORT, gui)).start()
    root.mainloop()

def start_tracker_server(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(10)
    print(f'Tracker server listening on {host}:{port}')

    while True:
        client_socket, _ = server.accept()
        threading.Thread(target=handle_client_connection, args=(client_socket,)).start()

def handle_client_connection(client_socket):
    data = client_socket.recv(1024).decode()
    if data == 'WORKER_REGISTER':
        handle_worker_connection(client_socket)
        show_workers()
    elif data == 'WORKER_UNREGISTER':
        handle_worker_unregistration(client_socket)
        show_workers()
    client_socket.close()

def handle_worker_unregistration(worker_socket):
    global WORKERS
    worker_ip = worker_socket.getpeername()[0]
    worker_socket.sendall(b'UNREGISTERED')
    WORKERS = [worker for worker in WORKERS if worker['ip'] != worker_ip]
    print(f'Worker {worker_ip} unregistered.')

def handle_worker_connection(worker_socket):
    global WORKERS
    worker_ip = worker_socket.getpeername()[0]
    worker_socket.sendall(b'REGISTERED')
    WORKERS.append({'ip': worker_ip, 'port': 5000})
    NUM_PARTS = len(WORKERS)
    print(f'Worker {worker_ip} registered.')


def start_coordinator():

    # create thread to keeoo track of workers
    
    threading.Thread(target=start_tracker_server, args=('0.0.0.0', 5002)).start()
    
    root = Tk()
    gui = CoordinatorGUI(root)
    
    root.mainloop()

if __name__ == "__main__":
    global NUM_PARTS

    NUM_PARTS = len(WORKERS)

    root = Tk()
    role_selector_gui = RoleSelectorGUI(root)
    root.mainloop()