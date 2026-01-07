# Personal Script Collection

A collection of Python automation scripts I wrote for fun to handle various small tasks.

## The System

These three files handle the logic to keep the folder portable without a massive single `requirements.txt`.

1.  **`install_dependencies.py` (The Installer)**
    * Analyzes a specific script to find what libraries it needs.
	* Checks if packages are missing and offers to `pip install` them.
    * Excludes local files from being wrongfully installed
		*Example: main.py includes `test` which is a local file `test.py`. The Installer does not attempt to run `pip install test`.

2.  **`run_file.py` (The Runner)**
    * Scans the directories for tools and presents a simple CLI menu.
    * Handles the execution flow.

3.  **`install_and_run_script` (Run & Install)**
    * `main.py` integrates the installer.
    * When you select a tool, it **first** runs the dependency check to ensure the environment is ready, **then** executes the script.

## Structure & Notes

* **General Folders:** My personal hobby code.
* **_EXE:** All my compiled `exe` files so i can easily access them without searching for them.
* **_Icons:** Icons for the `exe` files.
* **`_Antigravity`**: ⚠️ **Disclaimer:** This folder is 100% AI-generated experimental code. It does **not** reflect my actual coding style or skill level. It is purely a sandbox for testing LLM capabilities.