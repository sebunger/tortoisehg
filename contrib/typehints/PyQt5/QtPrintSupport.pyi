# The PEP 484 type hints stub file for the QtPrintSupport module.
#
# Generated by SIP 4.19.19
#
# Copyright (c) 2019 Riverbank Computing Limited <info@riverbankcomputing.com>
# 
# This file is part of PyQt5.
# 
# This file may be used under the terms of the GNU General Public License
# version 3.0 as published by the Free Software Foundation and appearing in
# the file LICENSE included in the packaging of this file.  Please review the
# following information to ensure the GNU General Public License version 3.0
# requirements will be met: http://www.gnu.org/copyleft/gpl.html.
# 
# If you do not wish to use this file under the terms of the GPL version 3.0
# then you may purchase a commercial license.  For more information contact
# info@riverbankcomputing.com.
# 
# This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
# WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.


import typing
import sip

from typing import overload

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

# Support for QDate, QDateTime and QTime.
import datetime

# Convenient type aliases.
PYQT_SIGNAL = typing.Union[QtCore.pyqtSignal, QtCore.pyqtBoundSignal]
PYQT_SLOT = typing.Union[typing.Callable[...], QtCore.pyqtBoundSignal]

# Convenient aliases for complicated OpenGL types.
PYQT_OPENGL_ARRAY = typing.Union[typing.Sequence[int], typing.Sequence[float],
        sip.Buffer, None]
PYQT_OPENGL_BOUND_ARRAY = typing.Union[typing.Sequence[int],
        typing.Sequence[float], sip.Buffer, int, None]


class QAbstractPrintDialog(QtWidgets.QDialog):

    PrintDialogOption: typing.Type[int]
    #class PrintDialogOption(int): ...
    None_ = ... # type: int
    PrintToFile = ... # type: int
    PrintSelection = ... # type: int
    PrintPageRange = ... # type: int
    PrintCollateCopies = ... # type: int
    PrintShowPageSize = ... # type: int
    PrintCurrentPage = ... # type: int

    PrintRange: typing.Type[int]
    #class PrintRange(int): ...
    AllPages = ... # type: int
    Selection = ... # type: int
    PageRange = ... # type: int
    CurrentPage = ... # type: int

    PrintDialogOptions: typing.Type[int]
    #class PrintDialogOptions(sip.simplewrapper):

        #@overload
        #def __init__(self) -> None: ...
        #@overload
        #def __init__(self, f: typing.Union[QAbstractPrintDialog.PrintDialogOptions, QAbstractPrintDialog.PrintDialogOption]) -> None: ...
        #@overload
        #def __init__(self, a0: QAbstractPrintDialog.PrintDialogOptions) -> None: ...

        #def __hash__(self) -> int: ...
        #def __bool__(self) -> int: ...
        #def __invert__(self) -> QAbstractPrintDialog.PrintDialogOptions: ...
        #def __int__(self) -> int: ...

    def __init__(self, printer: QPrinter, parent: typing.Optional[QtWidgets.QWidget] = ..., **props) -> None: ...

    def enabledOptions(self) -> int: ...
    def setEnabledOptions(self, options: typing.Union[int, int]) -> None: ...
    def setOptionTabs(self, tabs: typing.Iterable[QtWidgets.QWidget]) -> None: ...
    def printer(self) -> QPrinter: ...
    def toPage(self) -> int: ...
    def fromPage(self) -> int: ...
    def setFromTo(self, fromPage: int, toPage: int) -> None: ...
    def maxPage(self) -> int: ...
    def minPage(self) -> int: ...
    def setMinMax(self, min: int, max: int) -> None: ...
    def printRange(self) -> int: ...
    def setPrintRange(self, range: int) -> None: ...
    def exec(self) -> int: ...
    def exec_(self) -> int: ...


class QPageSetupDialog(QtWidgets.QDialog):

    @overload
    def __init__(self, printer: QPrinter, parent: typing.Optional[QtWidgets.QWidget] = ..., **props) -> None: ...
    @overload
    def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = ..., **props) -> None: ...

    def printer(self) -> QPrinter: ...
    def done(self, result: int) -> None: ...
    @overload
    def open(self) -> None: ...
    @overload
    def open(self, slot: PYQT_SLOT) -> None: ...
    def exec(self) -> int: ...
    def exec_(self) -> int: ...
    def setVisible(self, visible: bool) -> None: ...


class QPrintDialog(QAbstractPrintDialog):

    accepted: PYQT_SIGNAL

    @overload
    def __init__(self, printer: QPrinter, parent: typing.Optional[QtWidgets.QWidget] = ..., **props) -> None: ...
    @overload
    def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = ..., **props) -> None: ...

    #@overload
    #def accepted(self) -> None: ...
    #@overload
    #def accepted(self, printer: QPrinter) -> None: ...
    @overload
    def open(self) -> None: ...
    @overload
    def open(self, slot: PYQT_SLOT) -> None: ...
    def setVisible(self, visible: bool) -> None: ...
    def options(self) -> int: ...
    def setOptions(self, options: typing.Union[int, int]) -> None: ...
    def testOption(self, option: int) -> bool: ...
    def setOption(self, option: int, on: bool = ...) -> None: ...
    def done(self, result: int) -> None: ...
    def accept(self) -> None: ...
    def exec(self) -> int: ...
    def exec_(self) -> int: ...


class QPrintEngine(sip.simplewrapper):

    PrintEnginePropertyKey: typing.Type[int]
    #class PrintEnginePropertyKey(int): ...
    PPK_CollateCopies = ... # type: int
    PPK_ColorMode = ... # type: int
    PPK_Creator = ... # type: int
    PPK_DocumentName = ... # type: int
    PPK_FullPage = ... # type: int
    PPK_NumberOfCopies = ... # type: int
    PPK_Orientation = ... # type: int
    PPK_OutputFileName = ... # type: int
    PPK_PageOrder = ... # type: int
    PPK_PageRect = ... # type: int
    PPK_PageSize = ... # type: int
    PPK_PaperRect = ... # type: int
    PPK_PaperSource = ... # type: int
    PPK_PrinterName = ... # type: int
    PPK_PrinterProgram = ... # type: int
    PPK_Resolution = ... # type: int
    PPK_SelectionOption = ... # type: int
    PPK_SupportedResolutions = ... # type: int
    PPK_WindowsPageSize = ... # type: int
    PPK_FontEmbedding = ... # type: int
    PPK_Duplex = ... # type: int
    PPK_PaperSources = ... # type: int
    PPK_CustomPaperSize = ... # type: int
    PPK_PageMargins = ... # type: int
    PPK_PaperSize = ... # type: int
    PPK_CopyCount = ... # type: int
    PPK_SupportsMultipleCopies = ... # type: int
    PPK_PaperName = ... # type: int
    PPK_QPageSize = ... # type: int
    PPK_QPageMargins = ... # type: int
    PPK_QPageLayout = ... # type: int
    PPK_CustomBase = ... # type: int

    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, a0: QPrintEngine) -> None: ...

    def printerState(self) -> int: ...
    def metric(self, a0: int) -> int: ...
    def abort(self) -> bool: ...
    def newPage(self) -> bool: ...
    def property(self, key: int) -> typing.Any: ...
    def setProperty(self, key: int, value: typing.Any) -> None: ...


class QPrinter(QtGui.QPagedPaintDevice):

    DuplexMode: typing.Type[int]
    #class DuplexMode(int): ...
    DuplexNone = ... # type: int
    DuplexAuto = ... # type: int
    DuplexLongSide = ... # type: int
    DuplexShortSide = ... # type: int

    Unit: typing.Type[int]
    #class Unit(int): ...
    Millimeter = ... # type: int
    Point = ... # type: int
    Inch = ... # type: int
    Pica = ... # type: int
    Didot = ... # type: int
    Cicero = ... # type: int
    DevicePixel = ... # type: int

    PrintRange: typing.Type[int]
    #class PrintRange(int): ...
    AllPages = ... # type: int
    Selection = ... # type: int
    PageRange = ... # type: int
    CurrentPage = ... # type: int

    OutputFormat: typing.Type[int]
    #class OutputFormat(int): ...
    NativeFormat = ... # type: int
    PdfFormat = ... # type: int

    PrinterState: typing.Type[int]
    #class PrinterState(int): ...
    Idle = ... # type: int
    Active = ... # type: int
    Aborted = ... # type: int
    Error = ... # type: int

    PaperSource: typing.Type[int]
    #class PaperSource(int): ...
    OnlyOne = ... # type: int
    Lower = ... # type: int
    Middle = ... # type: int
    Manual = ... # type: int
    Envelope = ... # type: int
    EnvelopeManual = ... # type: int
    Auto = ... # type: int
    Tractor = ... # type: int
    SmallFormat = ... # type: int
    LargeFormat = ... # type: int
    LargeCapacity = ... # type: int
    Cassette = ... # type: int
    FormSource = ... # type: int
    MaxPageSource = ... # type: int
    Upper = ... # type: int
    CustomSource = ... # type: int
    LastPaperSource = ... # type: int

    ColorMode: typing.Type[int]
    #class ColorMode(int): ...
    GrayScale = ... # type: int
    Color = ... # type: int

    PageOrder: typing.Type[int]
    #class PageOrder(int): ...
    FirstPageFirst = ... # type: int
    LastPageFirst = ... # type: int

    Orientation: typing.Type[int]
    #class Orientation(int): ...
    Portrait = ... # type: int
    Landscape = ... # type: int

    PrinterMode: typing.Type[int]
    #class PrinterMode(int): ...
    ScreenResolution = ... # type: int
    PrinterResolution = ... # type: int
    HighResolution = ... # type: int

    @overload
    def __init__(self, mode: int = ...) -> None: ...
    @overload
    def __init__(self, printer: QPrinterInfo, mode: int = ...) -> None: ...

    def pdfVersion(self) -> int: ...
    def setPdfVersion(self, version: int) -> None: ...
    def paperName(self) -> str: ...
    def setPaperName(self, paperName: str) -> None: ...
    def setEngines(self, printEngine: QPrintEngine, paintEngine: QtGui.QPaintEngine) -> None: ...
    def metric(self, a0: int) -> int: ...
    def getPageMargins(self, unit: int) -> typing.Tuple[float, float, float, float]: ...
    def setPageMargins(self, left: float, top: float, right: float, bottom: float, unit: int) -> None: ...
    def setMargins(self, m: QtGui.QPagedPaintDevice.Margins) -> None: ...
    def printRange(self) -> int: ...
    def setPrintRange(self, range: int) -> None: ...
    def toPage(self) -> int: ...
    def fromPage(self) -> int: ...
    def setFromTo(self, fromPage: int, toPage: int) -> None: ...
    def printEngine(self) -> QPrintEngine: ...
    def paintEngine(self) -> QtGui.QPaintEngine: ...
    def printerState(self) -> int: ...
    def abort(self) -> bool: ...
    def newPage(self) -> bool: ...
    def setPrinterSelectionOption(self, a0: str) -> None: ...
    def printerSelectionOption(self) -> str: ...
    @overload
    def pageRect(self) -> QtCore.QRect: ...
    @overload
    def pageRect(self, a0: int) -> QtCore.QRectF: ...
    @overload
    def paperRect(self) -> QtCore.QRect: ...
    @overload
    def paperRect(self, a0: int) -> QtCore.QRectF: ...
    def doubleSidedPrinting(self) -> bool: ...
    def setDoubleSidedPrinting(self, enable: bool) -> None: ...
    def fontEmbeddingEnabled(self) -> bool: ...
    def setFontEmbeddingEnabled(self, enable: bool) -> None: ...
    def supportedResolutions(self) -> typing.List[int]: ...
    def duplex(self) -> int: ...
    def setDuplex(self, duplex: int) -> None: ...
    def paperSource(self) -> int: ...
    def setPaperSource(self, a0: int) -> None: ...
    def supportsMultipleCopies(self) -> bool: ...
    def copyCount(self) -> int: ...
    def setCopyCount(self, a0: int) -> None: ...
    def fullPage(self) -> bool: ...
    def setFullPage(self, a0: bool) -> None: ...
    def collateCopies(self) -> bool: ...
    def setCollateCopies(self, collate: bool) -> None: ...
    def colorMode(self) -> int: ...
    def setColorMode(self, a0: int) -> None: ...
    def resolution(self) -> int: ...
    def setResolution(self, a0: int) -> None: ...
    def pageOrder(self) -> int: ...
    def setPageOrder(self, a0: int) -> None: ...
    @overload
    def paperSize(self) -> int: ...
    @overload
    def paperSize(self, unit: int) -> QtCore.QSizeF: ...
    @overload
    def setPaperSize(self, a0: int) -> None: ...
    @overload
    def setPaperSize(self, paperSize: QtCore.QSizeF, unit: int) -> None: ...
    def setPageSizeMM(self, size: QtCore.QSizeF) -> None: ...
    def orientation(self) -> int: ...
    def setOrientation(self, a0: int) -> None: ...
    def creator(self) -> str: ...
    def setCreator(self, a0: str) -> None: ...
    def docName(self) -> str: ...
    def setDocName(self, a0: str) -> None: ...
    def printProgram(self) -> str: ...
    def setPrintProgram(self, a0: str) -> None: ...
    def outputFileName(self) -> str: ...
    def setOutputFileName(self, a0: str) -> None: ...
    def isValid(self) -> bool: ...
    def printerName(self) -> str: ...
    def setPrinterName(self, a0: str) -> None: ...
    def outputFormat(self) -> int: ...
    def setOutputFormat(self, format: int) -> None: ...


class QPrinterInfo(sip.simplewrapper):

    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, src: QPrinterInfo) -> None: ...
    @overload
    def __init__(self, printer: QPrinter) -> None: ...

    def supportedDuplexModes(self) -> typing.List[int]: ...
    def defaultDuplexMode(self) -> int: ...
    @staticmethod
    def defaultPrinterName() -> str: ...
    @staticmethod
    def availablePrinterNames() -> typing.List[str]: ...
    def supportedResolutions(self) -> typing.List[int]: ...
    def maximumPhysicalPageSize(self) -> QtGui.QPageSize: ...
    def minimumPhysicalPageSize(self) -> QtGui.QPageSize: ...
    def supportsCustomPageSizes(self) -> bool: ...
    def defaultPageSize(self) -> QtGui.QPageSize: ...
    def supportedPageSizes(self) -> typing.List[QtGui.QPageSize]: ...
    def state(self) -> int: ...
    def isRemote(self) -> bool: ...
    @staticmethod
    def printerInfo(printerName: str) -> QPrinterInfo: ...
    def makeAndModel(self) -> str: ...
    def location(self) -> str: ...
    def description(self) -> str: ...
    @staticmethod
    def defaultPrinter() -> QPrinterInfo: ...
    @staticmethod
    def availablePrinters() -> typing.List[QPrinterInfo]: ...
    def supportedSizesWithNames(self) -> typing.List[typing.Tuple[str, QtCore.QSizeF]]: ...
    def supportedPaperSizes(self) -> typing.List[int]: ...
    def isDefault(self) -> bool: ...
    def isNull(self) -> bool: ...
    def printerName(self) -> str: ...


class QPrintPreviewDialog(QtWidgets.QDialog):

    paintRequested: PYQT_SIGNAL

    @overload
    def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = ..., flags: typing.Union[int, int] = ..., **props) -> None: ...
    @overload
    def __init__(self, printer: QPrinter, parent: typing.Optional[QtWidgets.QWidget] = ..., flags: typing.Union[int, int] = ..., **props) -> None: ...

    #def paintRequested(self, printer: QPrinter) -> None: ...
    def done(self, result: int) -> None: ...
    def printer(self) -> QPrinter: ...
    @overload
    def open(self) -> None: ...
    @overload
    def open(self, slot: PYQT_SLOT) -> None: ...
    def setVisible(self, visible: bool) -> None: ...


class QPrintPreviewWidget(QtWidgets.QWidget):

    paintRequested: PYQT_SIGNAL
    previewChanged: PYQT_SIGNAL

    ZoomMode: typing.Type[int]
    #class ZoomMode(int): ...
    CustomZoom = ... # type: int
    FitToWidth = ... # type: int
    FitInView = ... # type: int

    ViewMode: typing.Type[int]
    #class ViewMode(int): ...
    SinglePageView = ... # type: int
    FacingPagesView = ... # type: int
    AllPagesView = ... # type: int

    @overload
    def __init__(self, printer: QPrinter, parent: typing.Optional[QtWidgets.QWidget] = ..., flags: typing.Union[int, int] = ..., **props) -> None: ...
    @overload
    def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = ..., flags: typing.Union[int, int] = ..., **props) -> None: ...

    def pageCount(self) -> int: ...
    #def previewChanged(self) -> None: ...
    #def paintRequested(self, printer: QPrinter) -> None: ...
    def updatePreview(self) -> None: ...
    def setAllPagesViewMode(self) -> None: ...
    def setFacingPagesViewMode(self) -> None: ...
    def setSinglePageViewMode(self) -> None: ...
    def setPortraitOrientation(self) -> None: ...
    def setLandscapeOrientation(self) -> None: ...
    def fitInView(self) -> None: ...
    def fitToWidth(self) -> None: ...
    def setCurrentPage(self, pageNumber: int) -> None: ...
    def setZoomMode(self, zoomMode: int) -> None: ...
    def setViewMode(self, viewMode: int) -> None: ...
    def setOrientation(self, orientation: int) -> None: ...
    def setZoomFactor(self, zoomFactor: float) -> None: ...
    def zoomOut(self, factor: float = ...) -> None: ...
    def zoomIn(self, factor: float = ...) -> None: ...
    def print(self) -> None: ...
    def print_(self) -> None: ...
    def setVisible(self, visible: bool) -> None: ...
    def currentPage(self) -> int: ...
    def zoomMode(self) -> int: ...
    def viewMode(self) -> int: ...
    def orientation(self) -> int: ...
    def zoomFactor(self) -> float: ...