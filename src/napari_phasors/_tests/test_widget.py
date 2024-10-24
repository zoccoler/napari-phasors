import os
from unittest.mock import MagicMock, patch

import numpy as np
import pandas.testing as pdt
from phasorpy.phasor import phasor_calibrate
from PyQt5.QtCore import QModelIndex
from qtpy.QtWidgets import QWidget

from napari_phasors._reader import napari_get_reader
from napari_phasors._synthetic_generator import (
    make_intensity_layer_with_phasors,
    make_raw_flim_data,
)
from napari_phasors._widget import (
    AdvancedOptionsWidget,
    CalibrationWidget,
    FbdWidget,
    LsmWidget,
    PhasorTransform,
    PtuWidget,
    WriterWidget,
)

TEST_FORMATS = [
    (".fbd", FbdWidget),
    (".ptu", PtuWidget),
    (".lsm", LsmWidget),
    (".ome.tif", None),
]


def test_phasor_trasfrom_widget(make_napari_viewer):
    """Test PhasorTransform widget call for specific file formats."""
    viewer = make_napari_viewer()
    widget = PhasorTransform(viewer)
    assert widget.viewer is viewer
    assert isinstance(widget, QWidget)
    model = MagicMock()
    current = MagicMock(spec=QModelIndex)

    for extension, expected_widget_class in TEST_FORMATS:
        with patch(
            "napari_phasors._widget._get_filename_extension",
            return_value=("filename", extension),
        ):
            if extension == ".fbd":
                model.filePath.return_value = (
                    "src/napari_phasors/_tests/test_data/test_file$EI0S.fbd"
                )
            else:
                model.filePath.return_value = (
                    f"src/napari_phasors/_tests/test_data/test_file{extension}"
                )
            for i in reversed(range(widget.dynamic_widget_layout.count())):
                widget_item = widget.dynamic_widget_layout.takeAt(i).widget()
                if widget_item:
                    widget_item.deleteLater()
            widget._on_change(current, model)
            if expected_widget_class:
                assert widget.dynamic_widget_layout.count() == 1
                added_widget = widget.dynamic_widget_layout.itemAt(0).widget()
                assert isinstance(added_widget, expected_widget_class)
            else:
                assert widget.dynamic_widget_layout.count() == 0


def test_phasor_transform_fbd_widget(make_napari_viewer):
    """Test FbdWidget from PhasorTransfrom widget."""
    viewer = make_napari_viewer()
    PhasorTransform(viewer)
    widget = FbdWidget(
        viewer, path="src/napari_phasors/_tests/test_data/test_file$EI0S.fbd"
    )
    assert widget.viewer is viewer
    # Init values
    assert isinstance(widget, AdvancedOptionsWidget)
    assert (
        widget.path == "src/napari_phasors/_tests/test_data/test_file$EI0S.fbd"
    )
    assert widget.reader_options == {"frame": -1, "channel": None}
    assert widget.harmonics == [1]
    assert widget.all_frames == 9
    assert widget.all_channels == 2
    assert widget.harmonic_start.value() == 1
    assert widget.harmonic_end.value() == 1
    # Modify harmonic values
    widget.harmonic_start.setValue(2)
    assert (
        widget.harmonic_start.value() == 2 and widget.harmonic_end.value() == 2
    )
    assert widget.harmonics == [2]
    widget.harmonic_end.setValue(3)
    assert (
        widget.harmonic_start.value() == 2 and widget.harmonic_end.value() == 3
    )
    assert widget.harmonics == [2, 3]
    # Init frames
    frames_combobox_values = [
        widget.frames.itemText(i) for i in range(widget.frames.count())
    ]
    assert frames_combobox_values == [
        "Average all frames",
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
    ]
    assert widget.frames.currentIndex() == 0
    # Modify frames
    widget.frames.setCurrentIndex(1)
    assert widget.reader_options == {"frame": 0, "channel": None}
    # Init channels
    channels_combobox_values = [
        widget.channels.itemText(i) for i in range(widget.channels.count())
    ]
    assert channels_combobox_values == ["All channels", "0", "1"]
    assert widget.channels.currentIndex() == 0
    # Modify channels
    widget.channels.setCurrentIndex(1)
    assert widget.reader_options == {"frame": 0, "channel": 0}
    # Click button of phasor transform and check layers
    widget.btn.click()
    assert len(viewer.layers) == 1
    assert viewer.layers[0].name == "test_file$EI0S Intensity Image: Channel 0"
    assert viewer.layers[0].data.shape == (1, 256, 256)
    phasor_data = (
        viewer.layers[0].metadata["phasor_features_labels_layer"].features
    )
    assert phasor_data.shape == (131072, 6)
    assert phasor_data["harmonic"].unique().tolist() == [2, 3]
    # Modify channels and harmonics and phasor transform again
    widget.channels.setCurrentIndex(0)
    widget.harmonic_end.setValue(2)
    widget.btn.click()
    assert len(viewer.layers) == 3
    assert viewer.layers[2].name == "test_file$EI0S Intensity Image: Channel 1"
    assert viewer.layers[2].data.shape == (1, 256, 256)
    phasor_data = (
        viewer.layers[2].metadata["phasor_features_labels_layer"].features
    )
    assert phasor_data.shape == (65536, 6)
    assert phasor_data["harmonic"].unique().tolist() == [2]
    # TODO: test laser factor parameter


def test_phasor_transform_ptu_widget(make_napari_viewer):
    """Test PtuWidget from PhasorTransfrom widget."""
    viewer = make_napari_viewer()
    PhasorTransform(viewer)
    widget = PtuWidget(
        viewer, path="src/napari_phasors/_tests/test_data/test_file.ptu"
    )
    assert widget.viewer is viewer
    # Init values
    assert isinstance(widget, AdvancedOptionsWidget)
    assert widget.path == "src/napari_phasors/_tests/test_data/test_file.ptu"
    assert widget.reader_options == {"frame": -1, "channel": None}
    assert widget.harmonics == [1]
    assert widget.all_frames == 5
    assert widget.all_channels == 1
    assert widget.harmonic_start.value() == 1
    assert widget.harmonic_end.value() == 1
    # Modify harmonic values
    widget.harmonic_start.setValue(2)
    assert (
        widget.harmonic_start.value() == 2 and widget.harmonic_end.value() == 2
    )
    assert widget.harmonics == [2]
    widget.harmonic_end.setValue(3)
    assert (
        widget.harmonic_start.value() == 2 and widget.harmonic_end.value() == 3
    )
    assert widget.harmonics == [2, 3]
    # Init frames
    frames_combobox_values = [
        widget.frames.itemText(i) for i in range(widget.frames.count())
    ]
    assert frames_combobox_values == [
        "Average all frames",
        "0",
        "1",
        "2",
        "3",
        "4",
    ]
    assert widget.frames.currentIndex() == 0
    # Modify frames
    widget.frames.setCurrentIndex(1)
    assert widget.reader_options == {"frame": 0, "channel": None}
    # Init channels
    channels_combobox_values = [
        widget.channels.itemText(i) for i in range(widget.channels.count())
    ]
    assert channels_combobox_values == ["All channels", "0"]
    assert widget.channels.currentIndex() == 0
    # Modify channels
    widget.channels.setCurrentIndex(1)
    assert widget.reader_options == {"frame": 0, "channel": 0}
    # Click button of phasor transform and check layers
    widget.btn.click()
    assert len(viewer.layers) == 1
    assert viewer.layers[0].name == "test_file Intensity Image: Channel 0"
    assert viewer.layers[0].data.shape == (1, 256, 256)
    phasor_data = (
        viewer.layers[0].metadata["phasor_features_labels_layer"].features
    )
    assert phasor_data.shape == (131072, 6)
    assert phasor_data["harmonic"].unique().tolist() == [2, 3]
    # Modify frames and harmonics and phasor transform again
    widget.frames.setCurrentIndex(0)
    widget.harmonic_end.setValue(2)
    widget.btn.click()
    assert len(viewer.layers) == 2
    assert viewer.layers[1].name == "test_file Intensity Image: Channel 0 [1]"
    assert viewer.layers[1].data.shape == (1, 256, 256)
    phasor_data = (
        viewer.layers[1].metadata["phasor_features_labels_layer"].features
    )
    assert phasor_data.shape == (65536, 6)
    assert phasor_data["harmonic"].unique().tolist() == [2]
    # TODO: test dtime parameter


def test_phasor_transform_lsm_widget(make_napari_viewer):
    """Test LsmWidget from PhasorTransfrom widget."""
    viewer = make_napari_viewer()
    PhasorTransform(viewer)
    widget = LsmWidget(
        viewer, path="src/napari_phasors/_tests/test_data/test_file.lsm"
    )
    assert widget.viewer is viewer
    # Init values
    assert isinstance(widget, AdvancedOptionsWidget)
    assert widget.path == "src/napari_phasors/_tests/test_data/test_file.lsm"
    assert widget.reader_options is None
    assert widget.harmonics == [1]
    assert widget.harmonic_start.value() == 1
    assert widget.harmonic_end.value() == 1
    # Modify harmonic values
    widget.harmonic_start.setValue(2)
    assert (
        widget.harmonic_start.value() == 2 and widget.harmonic_end.value() == 2
    )
    assert widget.harmonics == [2]
    widget.harmonic_end.setValue(3)
    assert (
        widget.harmonic_start.value() == 2 and widget.harmonic_end.value() == 3
    )
    assert widget.harmonics == [2, 3]
    # Click button of phasor transform and check layers
    widget.btn.click()
    assert len(viewer.layers) == 1
    assert viewer.layers[0].name == "test_file Intensity Image"
    assert viewer.layers[0].data.shape == (512, 512)
    phasor_data = (
        viewer.layers[0].metadata["phasor_features_labels_layer"].features
    )
    assert phasor_data.shape == (524288, 6)
    assert phasor_data["harmonic"].unique().tolist() == [2, 3]
    # Modify harmonics and phasor transform again
    widget.harmonic_end.setValue(2)
    widget.btn.click()
    assert len(viewer.layers) == 2
    assert viewer.layers[1].name == "test_file Intensity Image [1]"
    assert viewer.layers[1].data.shape == (512, 512)
    phasor_data = (
        viewer.layers[1].metadata["phasor_features_labels_layer"].features
    )
    assert phasor_data.shape == (262144, 6)
    assert phasor_data["harmonic"].unique().tolist() == [2]


def test_calibration_widget(make_napari_viewer):
    """Test the CalibrationWidget class."""
    # Create a synthetic FLIM data and an intensity image layer with phasors
    raw_flim_data = make_raw_flim_data()
    harmonic = [1, 2, 3]
    sample_image_layer = make_intensity_layer_with_phasors(
        raw_flim_data, harmonic=harmonic
    )
    # Create a synthetic calibration FLIM data and an calibration image layer
    raw_calibration_flim_data = make_raw_flim_data(
        shape=(2, 5), time_constants=[0.02, 0.2, 0.4, 1, 2, 4, 10, 20, 40, 100]
    )
    calibration_image_layer = make_intensity_layer_with_phasors(
        raw_calibration_flim_data, harmonic=harmonic
    )
    # Intialize viewer and add intensity image layer with phasors data
    viewer = make_napari_viewer()
    viewer.add_layer(sample_image_layer)
    viewer.add_layer(calibration_image_layer)
    original_phasors_table = sample_image_layer.metadata[
        "phasor_features_labels_layer"
    ].features
    original_mean = sample_image_layer.metadata["original_mean"]
    original_real = np.reshape(
        original_phasors_table["G_original"],
        (len(harmonic),) + original_mean.data.shape,
    )
    original_imag = np.reshape(
        original_phasors_table["S_original"],
        (len(harmonic),) + original_mean.data.shape,
    )
    calibration_phasors_table = calibration_image_layer.metadata[
        "phasor_features_labels_layer"
    ].features
    calibration_real = np.reshape(
        calibration_phasors_table["G_original"],
        (len(harmonic),) + original_mean.data.shape,
    )
    calibration_imag = np.reshape(
        calibration_phasors_table["S_original"],
        (len(harmonic),) + original_mean.data.shape,
    )
    sample_phasors_table = (
        viewer.layers[0].metadata["phasor_features_labels_layer"].features
    )
    pdt.assert_frame_equal(original_phasors_table, sample_phasors_table)
    # Check init calibration widget
    main_widget = CalibrationWidget(viewer)
    assert (
        main_widget.calibration_widget.frequency_line_edit_widget.text() == ""
    )
    assert (
        main_widget.calibration_widget.lifetime_line_edit_widget.text() == ""
    )
    assert "calibrated" not in viewer.layers[0].metadata.keys()
    assert "calibrated" not in viewer.layers[1].metadata.keys()
    sample_layer_combobox_items = [
        main_widget.calibration_widget.sample_layer_combobox.itemText(i)
        for i in range(
            main_widget.calibration_widget.sample_layer_combobox.count()
        )
    ]
    assert sample_image_layer.name in sample_layer_combobox_items
    assert calibration_image_layer.name in sample_layer_combobox_items
    calibration_layer_combobox_items = [
        main_widget.calibration_widget.calibration_layer_combobox.itemText(i)
        for i in range(
            main_widget.calibration_widget.calibration_layer_combobox.count()
        )
    ]
    assert calibration_image_layer.name in calibration_layer_combobox_items
    assert sample_image_layer.name in calibration_layer_combobox_items
    # Modify comboboxes selection, frequency and lifetime and calibrate
    main_widget.calibration_widget.sample_layer_combobox.setCurrentIndex(0)
    assert (
        main_widget.calibration_widget.sample_layer_combobox.currentText()
        == sample_image_layer.name
    )
    main_widget.calibration_widget.calibration_layer_combobox.setCurrentIndex(
        1
    )
    assert (
        main_widget.calibration_widget.calibration_layer_combobox.currentText()
        == calibration_image_layer.name
    )
    main_widget.calibration_widget.frequency_line_edit_widget.setText("80")
    assert (
        main_widget.calibration_widget.frequency_line_edit_widget.text()
        == "80"
    )
    main_widget.calibration_widget.lifetime_line_edit_widget.setText("2")
    assert (
        main_widget.calibration_widget.lifetime_line_edit_widget.text() == "2"
    )
    with patch("napari_phasors._widget.show_info") as mock_show_info:
        main_widget.calibration_widget.calibrate_push_button.click()
        sample_name = (
            main_widget.calibration_widget.sample_layer_combobox.currentText()
        )
        mock_show_info.assert_called_once_with(f"Calibrated {sample_name}")
    # Check if the calibration was successful
    assert viewer.layers[0].metadata["calibrated"] is True
    calibrated_real = np.reshape(
        viewer.layers[0]
        .metadata["phasor_features_labels_layer"]
        .features["G_original"],
        (len(harmonic),) + original_mean.data.shape,
    )
    calibrated_imag = np.reshape(
        viewer.layers[0]
        .metadata["phasor_features_labels_layer"]
        .features["S_original"],
        (len(harmonic),) + original_mean.data.shape,
    )
    expected_real, expected_imag = phasor_calibrate(
        original_real,
        original_imag,
        calibration_real,
        calibration_imag,
        frequency=80 * np.array(harmonic),
        lifetime=2,
        skip_axis=0,
    )
    assert np.allclose(calibrated_real, expected_real)
    assert np.allclose(calibrated_imag, expected_imag)
    with patch("napari_phasors._widget.show_error") as mock_show_error:
        main_widget.calibration_widget.calibrate_push_button.click()
        mock_show_error.assert_called_once_with("Layer already calibrated")


def test_writer_widget(make_napari_viewer, tmp_path):
    """Test the WriterWidget class."""
    # Intialize viewer and add intensity image layer with phasors data
    viewer = make_napari_viewer()
    main_widget = WriterWidget(viewer)
    assert main_widget.viewer is viewer
    assert isinstance(main_widget, QWidget)
    model = MagicMock()
    current = MagicMock(spec=QModelIndex)
    # Check init values are empty
    assert main_widget.save_path.text() == ""
    assert main_widget.export_layer_combobox.count() == 0
    assert main_widget.export_file_name.text() == ""
    # Create a synthetic FLIM data and an intensity image layer with phasors
    raw_flim_data = make_raw_flim_data()
    harmonic = [1, 2, 3]
    sample_image_layer = make_intensity_layer_with_phasors(
        raw_flim_data, harmonic=harmonic
    )
    viewer.add_layer(sample_image_layer)
    # Assert combobox is populated and file name is set
    assert (
        main_widget.export_layer_combobox.itemText(0)
        == sample_image_layer.name
    )
    assert (
        main_widget.export_layer_combobox.currentText()
        == sample_image_layer.name
    )
    assert main_widget.export_file_name.text() == sample_image_layer.name
    # Simulate a path selection from the search tree
    model.filePath.return_value = str(tmp_path)
    main_widget._on_search_tree_change(current, model)
    assert main_widget.save_path.text() == str(tmp_path)
    # Click export button and check if the file was created
    with patch("napari_phasors._widget.show_info") as mock_show_info:
        main_widget.btn.click()
        export_layer_name = main_widget.export_layer_combobox.currentText()
        export_path = os.path.join(
            main_widget.save_path.text(),
            f'{main_widget.export_file_name.text()}.ome.tif',
        )
        # Check if the show_info was called
        mock_show_info.assert_called_once_with(
            f"Exported {export_layer_name} to {export_path}"
        )
        # Check if the file was created and has expected data when read
        assert os.path.exists(export_path)
        reader = napari_get_reader(export_path, harmonics=harmonic)
        layer_data_list = reader(export_path)
        layer_data_tuple = layer_data_list[0]
        assert len(layer_data_tuple) == 2
        np.testing.assert_array_almost_equal(
            layer_data_tuple[0], sample_image_layer.data
        )
        phasor_features = layer_data_tuple[1]["metadata"][
            "phasor_features_labels_layer"
        ]
        np.testing.assert_array_equal(
            phasor_features.data, [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]]
        )
        assert phasor_features.features.shape == (30, 6)
        expected_columns = [
            "label",
            "G_original",
            "S_original",
            "G",
            "S",
            "harmonic",
        ]
        actual_columns = phasor_features.features.columns.tolist()
        assert actual_columns == expected_columns
        assert phasor_features.features["harmonic"].unique().tolist() == [
            1,
            2,
            3,
        ]
    # Check error messages if path or name are empty
    with patch("napari_phasors._widget.show_error") as mock_show_error:
        main_widget.save_path.setText("")
        main_widget.btn.click()
        mock_show_error.assert_called_once_with("Select export location")
        main_widget.save_path.setText(str(tmp_path))
        main_widget.export_file_name.setText("")
        main_widget.btn.click()
        mock_show_error.assert_called_with("Enter name of exported file")
