from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance
import maya.cmds as cm
import pymel.core as pm
import maya.OpenMaya as om
import maya.OpenMayaUI as omui
from maya.mel import eval
import os


# noinspection PyAttributeOutsideInit,PyMethodOverriding
class MixamoUI(QtWidgets.QDialog):
    fbxVersions = {
        '2016': 'FBX201600',
        '2014': 'FBX201400',
        '2013': 'FBX201300',
        '2017': 'FBX201700',
        '2018': 'FBX201800',
        '2019': 'FBX201900'
    }

    dlg_instance = None

    @classmethod
    def display(cls):
        if not cls.dlg_instance:
            cls.dlg_instance = MixamoUI()

        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()

        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    @classmethod
    def maya_main_window(cls):
        """

        Returns: The Maya main window widget as a Python object

        """
        main_window_ptr = omui.MQtUtil.mainWindow()
        return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)

    def __init__(self):
        super(MixamoUI, self).__init__(self.maya_main_window())

        self.setWindowTitle("Mixamo Export")

        # Eliminate help button
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.geometry = None

        # Set size of the UI
        self.setMinimumSize(300, 80)

        self.create_widget()
        self.create_layouts()
        self.create_connections()

    def create_widget(self):
        self.filepath_le = QtWidgets.QLineEdit()
        self.select_file_path_btn = QtWidgets.QPushButton('')
        self.select_file_path_btn.setIcon(QtGui.QIcon(':fileOpen.png'))
        self.select_file_path_btn.setToolTip('Select File')

        self.executed_btn = QtWidgets.QPushButton("Executed")
        self.close_btn = QtWidgets.QPushButton("Close")

    def create_layouts(self):
        filepath_layout = QtWidgets.QHBoxLayout()
        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow('File path:', self.filepath_le)

        filepath_layout.addLayout(form_layout)
        filepath_layout.addWidget(self.select_file_path_btn)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.executed_btn)
        button_layout.addWidget(self.close_btn)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(filepath_layout)
        main_layout.addLayout(button_layout)

    def create_connections(self):
        self.select_file_path_btn.clicked.connect(self.show_file_select_dialog)

        self.executed_btn.clicked.connect(self.executed)
        self.close_btn.clicked.connect(self.close)

    def show_file_select_dialog(self):
        self.filepath = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select directory', '/home')

        self.filepath_le.setText(self.filepath)

    def export_option(self, path):
        # Get maya version and fbx version
        version_maya = cm.about(version=True)
        self.version_fbx = self.fbxVersions.get(version_maya)

        # Option
        eval("FBXExportSmoothingGroups -v true")
        eval("FBXExportHardEdges -v false")
        eval("FBXExportTangents -v false")
        eval("FBXExportSmoothMesh -v true")
        eval("FBXExportInstances -v false")
        eval("FBXExportReferencedAssetsContent -v false")

        eval('FBXExportBakeComplexAnimation -v true')

        eval("FBXExportBakeComplexStep -v 1")

        eval("FBXExportUseSceneName -v false")
        eval("FBXExportQuaternion -v euler")
        eval("FBXExportShapes -v true")
        eval("FBXExportSkins -v true")

        # Constraints
        eval("FBXExportConstraints -v false")
        # Cameras
        eval("FBXExportCameras -v true")
        # Lights
        eval("FBXExportLights -v true")
        # Embed Media
        eval("FBXExportEmbeddedTextures -v true")
        # Connections
        eval("FBXExportInputConnections -v true")
        # Axis Conversion
        eval("FBXExportUpAxis y")
        # Version
        eval('FBXExportFileVersion -v {}'.format(self.version_fbx))

        # Export!
        eval('FBXExport -f "{0}" -s'.format(path))

    def check_parent(self):
        """

        Returns: List of joint who is children under world

        """
        # Get list of all joint in scene
        self.all_joints = pm.ls(type="joint")
        joint_under_world = []

        # Loop through all joint in list
        for joint in self.all_joints:

            # Check if the name "World" is exist or not
            if joint == "World":
                return om.MGlobal.displayError("This file already have world joint under world, please check it")

            # Check if joint is under world or not
            joint_parent = pm.listRelatives(joint, allParents=True)
            if len(joint_parent) == 0:
                joint_under_world.append(joint)
            else:
                continue

        # Return list of joint under world
        return joint_under_world

    def get_path_file_mixamo(self):
        """

        Returns: List of path to fbx file

        """
        # Get path of folder
        path = self.filepath_le.text()

        # Get all files path
        files = os.listdir(path)

        fbx_files_path = []

        # Loop through all files path
        for f in files:

            # Check if file is fbx or not
            if f.endswith(".fbx"):
                new_path = (os.path.join(path, f)).replace(os.sep, '/')
                fbx_files_path.append(new_path)
            else:
                continue

        # Return list of fbx files path
        return fbx_files_path

    def create_directory(self):
        """

        Returns: Create a folder to export new fbx file after fixing

        """
        # Get path of folder
        path = self.filepath_le.text()

        # Create a path to folder for export fbx
        self.directory = os.path.join(path, "MixamoExport")

        # Check folder is exist or not
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)

    def executed(self):
        # Create and check
        self.create_directory()

        # Get all files path
        file_path = self.get_path_file_mixamo()

        # Loop through all path
        for path in file_path:

            # Create new scene
            cm.file(force=True, newFile=True)

            # Rename path for maya can read
            new_path = path.replace("\\", "/")

            # Import fbx file into scene with out namespace
            cm.file(new_path, i=True, mergeNamespacesOnClash=True, namespace=':')

            # Get list joint under world
            list_joints = self.check_parent()

            # Create a world joint
            world_joint = pm.joint(n="World", r=True)

            # Loop through joint and parent it under world joint
            for joint in list_joints:
                pm.parent(joint, world_joint, relative=False)

            # Get fbx file name without the path
            fbxName = path.split("/")[-1]

            # Set path to new folder export we create
            path_fbx = (os.path.join(self.directory, fbxName)).replace(os.sep, '/')

            # Export fbx file
            pm.select(world_joint)
            self.export_option(path_fbx)

            # Create new scene again for clean maya
            cm.file(force=True, newFile=True)

    def showEvent(self, e):
        super(MixamoUI, self).showEvent(e)

        if self.geometry:
            self.restoreGeometry(self.geometry)

    def closeEvent(self, e):
        super(MixamoUI, self).closeEvent(e)

        self.geometry = self.saveGeometry()
