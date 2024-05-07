## Distributed Downloader

**DD** is a P2P software written in Python that utilizes a distributed divide-and-conquer approach to download large files. It works by splitting the file into smaller parts (download ranges) and assigning each part to a peer in the network for download. Participating peers then download their assigned parts locally and send them to the requesting client using a socket connection. Finally, the client merges the received parts to obtain the complete file.

### Architecture

DD functions within a local network of interconnected systems. There are three primary types of systems in a DD network:

* **Tracker Server:**  This system maintains information about participating systems. It stores the IP addresses of all peer servers within the network and provides this information to peer clients seeking distributed downloads.
* **Peer Server:**  These are systems within the network that assist peer clients with distributed downloads. They register themselves with the tracker server and actively listen for connections from clients. Upon exiting, peer servers send a `remove` request to the tracker, which subsequently removes them from the list of active servers. 
* **Peer Client:** These are systems within the network that intend to download a file using DD. They require the file URL for download. Peer clients query the tracker for available peer servers and assign download ranges for specific file parts to each server. Peer servers download their assigned ranges and send the file parts to the respective clients.

### Running DD

Here are some crucial points to consider before running DD:

* **Python 3 and pip:** Ensure you have Python 3 and pip (package installer) installed on all systems.
* **Network and OS:** It's recommended to test DD on a network with multiple Linux-based systems, each with an active internet connection.
* **Virtual Environment:**  Consider creating a Python virtual environment to isolate project dependencies using `requirements.txt`.
* **Elevated Privileges:**  `server.py` and `client.py` might require `sudo` permissions to create files and directories.

**Steps to Run:**

1. **Clone the Repository:** Clone the DD repository on all systems intended to participate in the download process.
2. **Navigate and Install Dependencies:** Open the terminal, navigate to the cloned DD directory, and run `pip install -r requirements.txt` to install required packages.
3. **Configuration (Optional):** For each system type (tracker, peer server, or peer client), you can configure settings using provided configuration files.
4. **Start Tracker:** Choose a system to act as the tracker. On that system, run `python tracker.py` to initiate the tracker server.
5. **Start Peer Servers:** On all other participating systems, run `python server.py` to start the peer server process.
6. **Download Initiation:** Select a system to download a file from the internet. To download a file using a sample URL like `https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_30mb.mp4`, run the following command:

```
python client.py https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_30mb.mp4
```

7. **Download Process:**  The distributed download process will commence. Upon successful completion (without errors), the downloaded file will be located in the download directory specified within the configuration file.

**Note:** DD is intended as a learning project and offers potential for further improvements. Feel free to experiment with DD, submit issues, request features, or contribute bug fixes.