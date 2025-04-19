# VisionHelp: An Assistive Vision System for Object Detection and Navigation

VisionHelp is an innovative assistive vision system designed to aid individuals with visual impairments. It combines object detection, depth estimation, and navigation guidance to provide users with a more interactive and accessible environment.

## Key Features

- **Object Detection**: Utilizes YOLOv5 for real-time object detection, identifying objects in video frames or images.
- **Depth Estimation**: Employs Depth-Anything V2 for estimating depth maps, allowing the system to assess object proximity.
- **Proximity Alerts**: Warns users of nearby objects based on customizable depth thresholds.
- **Navigation Guidance**: Provides compact directions to detected objects, helping users navigate their surroundings.

## How It Works

1. **Video Processing**: The system processes video frames, detecting objects and estimating their depth.
2. **Proximity Checks**: It checks if detected objects are within a safe distance, triggering audio warnings if necessary.
3. **User Interaction**: Users can request directions to specific objects by inputting their names.

## Requirements

- Python 3.x
- OpenCV
- PyTorch
- Pillow
- Ultralytics YOLOv5
- Hugging Face Transformers (for depth estimation)
- pyttsx3 (for text-to-speech functionality)

## Installation

1. Clone this repository.
2. Install required packages using `pip install -r requirements.txt`.
3. Ensure you have the necessary models downloaded (e.g., YOLOv5, Depth-Anything V2).

## Usage

1. Run the main script to start the video processing loop.
2. Press 'c' to enter interactive mode and request directions to objects.

## Example Use Cases

- **Assistive Technology**: VisionHelp can be integrated into wearable devices or smart home systems to enhance accessibility.
- **Safety Applications**: It can be used in environments where proximity awareness is crucial, such as warehouses or construction sites.

## Contributing

Contributions are welcome! Feel free to submit pull requests or open issues to discuss improvements.

### Acknowledgments

- **Ultralytics**: For providing the YOLOv5 model.
- **Hugging Face**: For the Depth-Anything V2 model.
- **pyttsx3**: For text-to-speech functionality.

---
