from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from converter import ConversionRequest, available_targets, execute

class ConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Converter")
        self.root.geometry("600x450")
        
        self.source_path = None
        self.output_dir = Path("./output")
        self.output_dir.mkdir(exist_ok=True)
        
        self.file_path_var = tk.StringVar(value="No file selected")
        self.output_path_var = tk.StringVar(value=str(self.output_dir.resolve()))
        
        self.create_widgets()

    def create_widgets(self):
        # Input
        frame_input = ttk.LabelFrame(self.root, text="Input File", padding=10)
        frame_input.pack(fill="x", padx=10, pady=5)
        
        self.btn_browse = ttk.Button(frame_input, text="Browse...", command=self.select_file)
        self.btn_browse.pack(side="left", padx=5)
        
        self.entry_file = ttk.Entry(frame_input, textvariable=self.file_path_var, state="readonly")
        self.entry_file.pack(side="left", padx=5, fill="x", expand=True)

        # Output
        frame_output = ttk.LabelFrame(self.root, text="Output Directory", padding=10)
        frame_output.pack(fill="x", padx=10, pady=5)
        
        self.btn_output = ttk.Button(frame_output, text="Browse...", command=self.select_output_dir)
        self.btn_output.pack(side="left", padx=5)
        
        self.entry_output = ttk.Entry(frame_output, textvariable=self.output_path_var, state="readonly")
        self.entry_output.pack(side="left", padx=5, fill="x", expand=True)

        # Target format
        frame_target = ttk.LabelFrame(self.root, text="Target Format", padding=10)
        frame_target.pack(fill="x", padx=10, pady=5)
        
        self.combo_targets = ttk.Combobox(frame_target, state="readonly")
        self.combo_targets.pack(fill="x", padx=5)

        # Actions
        frame_action = ttk.Frame(self.root, padding=10)
        frame_action.pack(fill="x", padx=10, pady=10)
        
        self.btn_convert = ttk.Button(frame_action, text="Convert", command=self.convert, state="disabled")
        self.btn_convert.pack(fill="x", padx=5)

        # Log
        frame_log = ttk.LabelFrame(self.root, text="Status Log", padding=10)
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.txt_log = tk.Text(frame_log, height=5, state="disabled")
        self.txt_log.pack(fill="both", expand=True)

    def select_file(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.source_path = Path(filename)
            self.file_path_var.set(str(self.source_path))
            
            targets = available_targets(self.source_path)
            self.combo_targets['values'] = targets
            if targets:
                self.combo_targets.current(0)
                self.btn_convert.config(state="normal")
            else:
                self.combo_targets.set('')
                self.btn_convert.config(state="disabled")
                messagebox.showwarning("Warning", "Unsupported file type!")

    def select_output_dir(self):
        dirname = filedialog.askdirectory()
        if dirname:
            self.output_dir = Path(dirname)
            self.output_path_var.set(str(self.output_dir.resolve()))

    def log(self, message):
        self.txt_log.config(state="normal")
        self.txt_log.insert("end", message + "\n")
        self.txt_log.see("end")
        self.txt_log.config(state="disabled")

    def convert(self):
        if not self.source_path:
            return
        
        target_format = self.combo_targets.get()
        if not target_format:
            messagebox.showerror("Error", "Please select a target format!")
            return
            
        target_filename = f"{self.source_path.stem}{target_format}"
        target_path = self.output_dir / target_filename
        
        if target_path.exists():
            overwrite = messagebox.askyesno(
                "File Exists",
                f"File '{target_filename}' already exists.\nDo you want to overwrite it?"
            )
            if not overwrite:
                return

        request = ConversionRequest(
            source=self.source_path,
            target_format=target_format,
            output_dir=self.output_dir
        )
        
        try:
            result_path = execute(request)
            self.log(f"Success: {result_path.name}")
            messagebox.showinfo("Success", f"File converted successfully:\n{result_path}")
        except Exception as e:
            self.log(f"Error: {e}")
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = ConverterApp(root)
    root.mainloop()