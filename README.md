# Omniscient Cinema 4D &middot; [![GitHub license](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

A plugin to easily import tracking data and LiDAR scans recorded with the [Omniscient iOS app](https://omniscient-app.com/), into Cinema 4D.

## Installation

To install the Omniscient Cinema 4D plugin, follow these steps:

1. Download the latest release from the [releases page](https://github.com/Stellaxis/omniscient-cinema4D/releases).
2. Extract the downloaded .zip file.
3. Move the extracted folder to your Cinema 4D plugins directory.
4. Restart Cinema 4D to load the new plugin.

Verify that the plugin is loaded successfully by checking if the "Omniscient Importer" is present in the Extensions menu.

## Usage

To use the Omniscient Cinema 4D plugin, follow these steps:

1. Open the [Omniscient iOS app](https://omniscient-app.com/) and capture your shots.
2. From the iOS app, export your shots with at least the following options selected:

<table>
  <tr>
    <td><strong>Video</strong></td>
    <td>Source</td>
  </tr>
  <tr>
    <td><strong>Camera</strong></td>
    <td>.abc</td>
  </tr>
  <tr>
    <td><strong>Geometry</strong></td>
    <td>.obj</td>
  </tr>
  <tr>
    <td><strong>Third-party</strong></td>
    <td>C4D</td>
  </tr>
</table>

3. In Cinema 4D, you can either:
   - **Drag and Drop**: Simply drag and drop the `.omni` file into the scene.
   - **Menu Import**: Go to `Extensions > Omniscient Importer` and select the `.omni` file you exported.
4. The camera, mesh, and video will be automatically imported into your scene.

## Compatibility

- **Tested Cinema 4D Versions**: 2023.2, 2024.0.2
- **Supported Omniscient iOS Version**: 1.14.0 or higher

## Support

For support with the Omniscient Cinema 4D plugin, please contact us through our [website](https://omniscient-app.com/) or open an issue on the [GitHub repository](https://github.com/Stellaxis/omniscient-cinema4d/issues).

## Contributing

We welcome contributions to the Omniscient Cinema 4D plugin.

## License

The Omniscient Cinema 4D plugin is licensed under the [Apache-2.0 License](LICENSE).