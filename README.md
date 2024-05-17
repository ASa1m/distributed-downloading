# Distributed Downloading System

## Table of Contents
1. Introduction
2. System Overview
3. Project Structure
4. Coordinator Module
5. Worker Module
6. GUI Module
7. Dependencies
8. Running the Project
9. Future Improvements

---

## 1. Introduction

This project demonstrates a distributed downloading system where multiple worker nodes download different parts of a file concurrently and send them to a coordinator node for assembly. The system aims to accelerate file downloading by leveraging parallel processing across multiple machines.

---

## 2. System Overview

The system consists of three main components:
1. **Coordinator**: The central node responsible for dividing the file into parts, dispatching download tasks to worker nodes, and assembling the downloaded parts into the final file.
2. **Worker**: Nodes that receive download tasks, download specific parts of the file, and send the parts back to the coordinator.
3. **GUI**: A graphical user interface that allows users to select roles (Coordinator/Worker) and monitor the download progress.

---

## 3. Project Structure

The project is structured into several modules to separate functionalities and enhance maintainability:

- `main.py`: The main and only file having following classes:
    - `Coordinator`: Class for the coordinator node.
    - `Worker`: Class for the worker node.
    - `RoleSelectorGUI`: Class for the role selection GUI.
    - `WorkerGUI`: Class for the worker GUI.
    - `CoordinatorGUI`: Class for the coordinator GUI.


### File Structure

```
distributed-downloading/
├── main.py
```

---

## 4. Coordinator Module

### Responsibilities
- Dividing the file into parts based on its size.
- Sending download tasks to worker nodes.
- Receiving downloaded parts from workers.
- Combining the received parts into the final file.

### Key Functions

- `get_file_size(url)`: Fetches the size of the file to be downloaded.
- `receive_part(part_num)`: Listens for incoming connections from workers to receive file parts.
- `combine_parts(output_file, num_parts)`: Combines all parts into the final file.
- `start_distributed_download(url, output_file, num_parts, workers)`: Orchestrates the entire download process.

---

## 5. Worker Module

### Responsibilities
- Receiving download tasks from the coordinator.
- Downloading specified parts of the file.
- Sending the downloaded parts back to the coordinator.

### Key Functions

- `download_part(url, start, end, part_num, coordinator_ip)`: Downloads a specified part of the file.
- `send_part_to_coordinator(file_name, part_num, coordinator_ip)`: Sends the downloaded part back to the coordinator.
- `handle_task(task, coordinator_ip)`: Handles the task received from the coordinator.
- `start_worker_server(host, port, coordinator_ip)`: Starts the worker server to listen for tasks from the coordinator.

---

## 6. GUI Module

### Responsibilities
- Providing a user interface for role selection.
- Allowing input of coordinator IP address for worker nodes.
- Displaying download progress and statuses.

### Key Functions

- `RoleSelectorGUI`: Class for the initial role selection interface.
- `get_coordinator_ip()`: Prompts user to enter the coordinator IP.
- `start_worker(coordinator_ip)`: Initiates the worker process.
- `start_coordinator()`: Initiates the coordinator process.

---

## 7. Dependencies

Ensure the following Python packages are installed:

- `requests`
- `socket`
- `threading`
- `tqdm`
- `tkinter`

You can install them using:
```sh
pip install requests tqdm
```

---

## 8. Running the Project

### Step 1: Start the Coordinator
Run the `main.py` script and select the "Coordinator" role. The coordinator will divide the file into parts and wait for workers to connect.

### Step 2: Start the Workers
Run the `main.py` script on worker machines, select the "Worker" role, and enter the coordinator's IP address. Each worker will start downloading its assigned part of the file and send it back to the coordinator.

### Step 3: Monitor the Progress
The GUI will display the progress of file downloading and combining operations. 

---

## 9. Future Improvements

- **Dynamic Worker Allocation**: Implement dynamic allocation and load balancing for worker nodes.
- **Error Handling**: Enhance error handling mechanisms for network interruptions and file I/O issues.
- **Security**: Implement security measures such as SSL for secure communication between nodes.
- **Scalability**: Optimize the system for handling larger files and more worker nodes.
- **Configuration**: Add a configuration file for easy setup and customization.