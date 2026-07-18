"""ChArUco board construction from a CalibrationMat.board_spec payload.

board_spec (schema_version 1):
  {"schema_version": 1, "squares_x": 14, "squares_y": 10,
   "square_mm": 100.0, "marker_mm": 75.0, "aruco_dict": "DICT_5X5_1000"}
"""
import cv2


def build_board(spec):
    name = spec.get('aruco_dict', 'DICT_5X5_1000')
    dict_id = getattr(cv2.aruco, name)          # unknown name -> AttributeError, honest
    adict = cv2.aruco.getPredefinedDictionary(dict_id)
    return cv2.aruco.CharucoBoard(
        (int(spec['squares_x']), int(spec['squares_y'])),
        float(spec['square_mm']), float(spec['marker_mm']), adict)


def board_size_mm(spec):
    return (spec['squares_x'] * spec['square_mm'],
            spec['squares_y'] * spec['square_mm'])
