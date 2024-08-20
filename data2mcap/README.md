# Data to MCap Converter

This is a simple python script that converts images to mcap.

## Usage

- Clone the repository and navigate to the current directory.
- (Optional) Create a virtual environment and activate it.
- Install the required packages using the following command:
  ```bash
  pip install -r requirements.txt
  ```
- Run the script using the following command:

  ```bash
  python image_to_mcap.py <input_directory> <output_directory>
  ```

  The script will:

  - Find all subdirectories that starts with `sample`
  - For each sample directory, a conversion will be made, outputting the mcap result in the `<output_directory>`, each having a different name dependent on the relative path to `<intput_directory>`.
  - For each conversion, all `.png` images in the sample directory will be converted to `foxglove.CompressedImage` message.
    - It is assumed that all such images have the timestamp (in millisecond) as the filename. E.g. `<ts>.png`.
    - The topic name of image message will be the relative path of the image's parent directory to the sample directory. E.g. `sample1/a/b/ts.png` will have the topic name `a/b`.

- View the output mcap files in the `<output_directory>`. The mcap files will be named as `<output_directory>/<relative_path>.mcap`.
