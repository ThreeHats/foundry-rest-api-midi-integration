# Foundry VTT MIDI REST API Integration

[![Demo video vink](https://img.youtube.com/vi/8ISvtMumBYc/0.jpg)](https://www.youtube.com/shorts/8ISvtMumBYc)

A desktop application that allows you to control Foundry VTT using MIDI controllers. Map MIDI buttons, knobs, and keys to specific REST API endpoints in Foundry VTT to trigger dice rolls, macros, and other actions.

<img width="1907" height="1034" alt="foundry-rest-api-midi-integration" src="https://github.com/user-attachments/assets/aac8d139-1096-418d-b1a3-4492d316cca2" />

## Features

- Connect any MIDI device to Foundry VTT
- Map MIDI signals (note on/off, control change) to API endpoints
- Configure API endpoint parameters for each mapping
- Monitor MIDI signals in real-time
- Save and load mapping configurations
- Low-latency operation for responsive gameplay
- User-friendly interface with MIDI learning capability

## Installation

### Prerequisites

- Python 3.8 or higher
- PyQt6
- A MIDI controller device
- Foundry VTT with REST API module installed

### Setup

1. Clone this repository:
   ```
   git clone https://github.com/your-username/foundry-rest-api-midi-integration.git
   cd foundry-rest-api-midi-integration
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python main.py
   ```

   For development mode with detailed logging:
   ```
   python main.py --dev
   ```

## Usage

### Initial Configuration

1. **Configure API Connection**:
   - Go to the "Configuration" tab
   - Enter your Foundry VTT REST API URL (e.g., `http://localhost:3010`)
   - Enter your API key
   - Click "Test Connection"
   - Select your Foundry VTT world (client)
   - Click "Save Configuration"

2. **Connect MIDI Device**:
   - Go to the "MIDI Mappings" tab
   - Select your MIDI device from the dropdown
   - Click "Connect"

### Creating Mappings

1. **Manual Mapping**:
   - Select the MIDI signal type (note_on, note_off, control_change)
   - Enter the channel and note/control number
   - Select an API endpoint from the dropdown
   - Configure parameters if required
   - Click "Add Mapping"

2. **Using MIDI Learn**:
   - Click "MIDI Learn"
   - Press the button on your MIDI controller you want to map
   - Select an API endpoint from the dropdown
   - Configure parameters if required
   - Click "Add Mapping"

### Managing Mappings

- **Edit Mapping**: Select a mapping and click "Edit Parameters" to modify API parameters
- **Delete Mapping**: Select a mapping and click "Delete Selected Mapping"
- **Import/Export**: Use the buttons at the bottom of the main window to import or export mapping configurations

## API Endpoints

The application supports all endpoints provided by the Foundry VTT REST API module. Common endpoints include:

- `/roll`: Make dice rolls
- `/entity`: Create entities
- `/get/:uuid`: Get entity data
- `/search`: Search for entities
- `/sheet/:uuid`: Get character sheet

## Command Line Options

- `--dev`: Enable development mode with detailed logging

## Troubleshooting

### MIDI Device Not Detected

1. Make sure your MIDI device is connected before starting the application
2. Click the "Refresh Devices" button to re-scan for MIDI devices
3. Try disconnecting and reconnecting your MIDI device

### API Connection Issues

1. Verify your API URL is correct and includes the port if necessary
2. Ensure your API key is valid
3. Check that the REST API module is enabled in your Foundry VTT world
4. Verify network connectivity between your computer and Foundry server
5. Try reloading the foundry world

### Performance Issues

If you experience delays between button presses and actions:

1. Run the application without the `--dev` flag to disable detailed logging
2. Close the MIDI Monitor tab if not needed

## Data Storage

Configuration data is stored in the following locations:

- Settings: User preferences stored via QSettings
- Mappings: JSON file stored in `~/.foundry_midi_rest/mappings.json`
- Logs: Log files stored in `~/.foundry_midi_rest/logs/` (when using `--dev` mode)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Foundry VTT](https://foundryvtt.com/)
- [Foundry VTT REST API Module](https://github.com/ThreeHats/foundryvtt-rest-api)
- [MIDO Python MIDI Library](https://mido.readthedocs.io/)
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
