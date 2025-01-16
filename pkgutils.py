#!/usr/bin/env python3
"""
novelWriter – Packaging Utils
=============================

File History:
Created: 2019-05-16 [0.5.1]
Renamed: 2023-07-26 [2.1b1]
Split:   2025-01-16 [2.7b1]

This file is a part of novelWriter
Copyright (C) 2019 Veronica Berglyd Olsen and novelWriter contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
from __future__ import annotations

import argparse
import datetime
import email.utils
import shutil
import subprocess
import sys
import zipfile

from pathlib import Path

import utils.binary_dist
import utils.icon_themes
import utils.windows_build

from utils.common import (
    ROOT_DIR, SETUP_DIR, checkAssetsExist, copySourceCode, extractVersion,
    makeCheckSum, readFile, stripVersion, toUpload, writeFile
)

SIGN_KEY = "D6A9F6B8F227CF7C6F6D1EE84DBBE4B734B0BD08"

OS_LINUX = sys.platform.startswith("linux")
OS_DARWIN = sys.platform.startswith("darwin")
OS_WIN = sys.platform.startswith("win32")


##
#  Print Version
##

def printVersion(args: argparse.Namespace) -> None:
    """Print the novelWriter version and exit."""
    print(extractVersion(beQuiet=True)[0], end=None)
    return


##
# Package Installer (pip)
##

def installPackages(args: argparse.Namespace) -> None:
    """Install package dependencies both for this script and for running
    novelWriter itself.
    """
    print("")
    print("Installing Dependencies")
    print("=======================")
    print("")

    installQueue = ["pip", "-r requirements.txt"]
    if args.mac:
        installQueue.append("pyobjc")
    elif args.win:
        installQueue.append("pywin32")

    pyCmd = [sys.executable, "-m"]
    pipCmd = ["pip", "install", "--user", "--upgrade"]
    for stepCmd in installQueue:
        pkgCmd = stepCmd.split(" ")
        try:
            subprocess.call(pyCmd + pipCmd + pkgCmd)
        except Exception as exc:
            print("Failed with error:")
            print(str(exc))
            sys.exit(1)

    return


##
#  Clean Build and Dist Folders (build-clean)
##

def cleanBuildDirs(args: argparse.Namespace) -> None:
    """Recursively delete the 'build' and 'dist' folders."""
    print("")
    print("Cleaning up build environment ...")
    print("")

    folders = [
        ROOT_DIR / "build",
        ROOT_DIR / "build_bin",
        ROOT_DIR / "dist",
        ROOT_DIR / "dist_bin",
        ROOT_DIR / "dist_deb",
        ROOT_DIR / "dist_minimal",
        ROOT_DIR / "dist_appimage",
        ROOT_DIR / "novelWriter.egg-info",
    ]

    for folder in folders:
        if folder.is_dir():
            try:
                shutil.rmtree(folder)
                print("Deleted: %s" % folder)
            except OSError:
                print("Failed:  %s" % folder)
        else:
            print("Missing: %s" % folder)

    print("")

    return


# =============================================================================================== #
#  Additional Builds
# =============================================================================================== #

##
#  Build PDF Manual (manual)
##

def buildPdfManual(args: argparse.Namespace | None = None) -> None:
    """This function will build the documentation as manual.pdf."""
    print("")
    print("Building PDF Manual")
    print("===================")
    print("")

    buildFile = ROOT_DIR / "docs" / "build" / "latex" / "manual.pdf"
    finalFile = ROOT_DIR / "novelwriter" / "assets" / "manual.pdf"
    finalFile.unlink(missing_ok=True)

    try:
        subprocess.call(["make", "clean"], cwd="docs")
        exCode = subprocess.call(["make", "latexpdf"], cwd="docs")
        if exCode == 0:
            print("")
            buildFile.rename(finalFile)
        else:
            raise Exception(f"Build returned error code {exCode}")

        print("PDF manual build: OK")
        print("")

    except Exception as exc:
        print("PDF manual build: FAILED")
        print("")
        print(str(exc))
        print("")
        print("Dependencies:")
        print(" * pip install sphinx")
        print(" * Package latexmk")
        print(" * LaTeX build system")
        print("")
        print(" On Debian/Ubuntu, install: python3-sphinx latexmk texlive texlive-latex-extra")
        print("")
        sys.exit(1)

    if not finalFile.is_file():
        print("No output file was found!")
        print("")
        sys.exit(1)

    return


##
#  Sample Project ZIP File Builder (sample)
##

def buildSampleZip(args: argparse.Namespace | None = None) -> None:
    """Bundle the sample project into a single zip file to be saved into
    the novelwriter/assets folder for further bundling into builds.
    """
    print("")
    print("Building Sample ZIP File")
    print("========================")
    print("")

    srcSample = ROOT_DIR / "sample"
    dstSample = ROOT_DIR / "novelwriter" / "assets" / "sample.zip"

    if srcSample.is_dir():
        dstSample.unlink(missing_ok=True)
        with zipfile.ZipFile(dstSample, "w") as zipObj:
            print("Compressing: nwProject.nwx")
            zipObj.write(srcSample / "nwProject.nwx", "nwProject.nwx")
            for doc in (srcSample / "content").iterdir():
                print(f"Compressing: content/{doc.name}")
                zipObj.write(doc, f"content/{doc.name}")

    else:
        print("Error: Could not find sample project source directory.")
        sys.exit(1)

    print("")
    print("Built file: %s" % dstSample)
    print("")

    return


##
#  Import Translations (import-i18n)
##

def importI18nUpdates(args: argparse.Namespace) -> None:
    """Import new translation files from a zip file."""
    print("")
    print("Import Updated Translations")
    print("===========================")
    print("")

    fileName = Path(args.file).absolute()
    if not fileName.is_file():
        print("File not found ...")
        sys.exit(1)

    dstPath = ROOT_DIR / "novelwriter" / "assets" / "i18n"
    srcPath = ROOT_DIR / "i18n"

    print(f"Loading file: {fileName}")
    with zipfile.ZipFile(fileName) as zipObj:
        for item in zipObj.namelist():
            if item.startswith("nw_") and item.endswith(".ts"):
                zipObj.extract(item, srcPath)
                print(f"Extracted: {item} > {srcPath / item}")
            elif item.startswith("project_") and item.endswith(".json"):
                zipObj.extract(item, dstPath)
                print(f"Extracted: {item} > {dstPath / item}")
            else:
                print(f"Skipped: {item}")

    print("")

    return


##
#  Qt Linguist TS Builder (qtlupdate)
##

def updateTranslationSources(args: argparse.Namespace) -> None:
    """Build the lang.ts files for Qt Linguist."""
    print("")
    print("Building Qt Translation Files")
    print("=============================")

    try:
        # Using the pylupdate tool from PyQt6 as it supports TS file format 2.1.
        from PyQt6.lupdate.lupdate import lupdate
    except ImportError:
        print("ERROR: This command requires lupdate from PyQt6")
        print("On Debian/Ubuntu, install: pyqt6-dev-tools")
        sys.exit(1)

    print("")
    print("Scanning Source Tree:")
    print("")

    sources = list((ROOT_DIR / "novelwriter").glob("**/*.py"))
    sources.insert(0, ROOT_DIR / "i18n" / "qtbase.py")
    for source in sources:
        print(source.relative_to(ROOT_DIR))

    print("")
    print("TS Files to Update:")
    print("")

    translations = []
    for item in [Path(str(f)).absolute() for f in args.files]:
        if not (item.name.startswith("nw_") and item.suffix == ".ts"):
            print(f"Skipped: {item}")
            continue

        if item.is_file():
            translations.append(item)
            print(f"Added: {item}")
        elif item.exists():
            continue
        else:  # Create an empty new language file
            langCode = item.name[3:-3]
            writeFile(item, (
                "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
                "<!DOCTYPE TS>\n"
                f"<TS version=\"2.0\" language=\"{langCode}\" sourcelanguage=\"en_GB\"/>\n"
            ))
            translations.append(item)
            print(f"Created: {item}")

    print("")
    print("Updating Language Files:")
    print("")

    lupdate(
        sources=[str(f) for f in sources],
        translation_files=[str(f) for f in translations],
        no_obsolete=True,
        no_summary=False,
    )

    print("")

    return


##
#  Qt Linguist QM Builder (qtlrelease)
##

def buildTranslationAssets(args: argparse.Namespace | None = None) -> None:
    """Build the lang.qm files for Qt Linguist."""
    print("")
    print("Building Qt Localisation Files")
    print("==============================")

    print("")
    print("TS Files to Build:")
    print("")

    srcDir = ROOT_DIR / "i18n"
    dstDir = ROOT_DIR / "novelwriter" / "assets" / "i18n"

    srcList = []
    for item in srcDir.iterdir():
        if item.is_file() and item.suffix == ".ts" and item.name != "nw_base.ts":
            srcList.append(item)
            print(item)

    print("")
    print("Building Translation Files:")
    print("")

    try:
        subprocess.call(["lrelease", "-verbose", *srcList])
    except Exception as exc:
        print("Qt Linguist tools seem to be missing")
        print("On Debian/Ubuntu, install: qttools5-dev-tools")
        print(str(exc))
        sys.exit(1)

    print("")
    print("Moving QM Files to Assets")
    print("")

    dstRel = dstDir.relative_to(ROOT_DIR)
    for item in srcDir.iterdir():
        if item.is_file() and item.suffix == ".qm":
            item.rename(dstDir / item.name)
            print("Moved: %s -> %s" % (item.relative_to(ROOT_DIR), dstRel / item.name))

    print("")

    return


##
#  Clean Assets (clean-assets)
##

def cleanBuiltAssets(args: argparse.Namespace | None = None) -> None:
    """Remove assets built by this script."""
    print("")
    print("Removing Built Assets")
    print("=====================")
    print("")

    assets = [
        ROOT_DIR / "novelwriter" / "assets" / "sample.zip",
        ROOT_DIR / "novelwriter" / "assets" / "manual.pdf",
    ]
    assets.extend((ROOT_DIR / "novelwriter" / "assets" / "i18n").glob("*.qm"))
    for asset in assets:
        if asset.is_file():
            asset.unlink()
            print(f"Deleted: {asset.relative_to(ROOT_DIR)}")

    print("")

    return


##
#  Build Assets (build-assets)
##

def buildAllAssets(args: argparse.Namespace) -> None:
    """Build all assets."""
    cleanBuiltAssets()
    buildPdfManual()
    buildSampleZip()
    buildTranslationAssets()
    return


# =============================================================================================== #
#  Python Packaging
# =============================================================================================== #

##
#  Copy Package Files
##

def copyPackageFiles(dst: Path, setupPy: bool = False) -> None:
    """Copy files needed for packaging."""

    copyFiles = ["LICENSE.md", "CREDITS.md", "pyproject.toml"]
    for copyFile in copyFiles:
        shutil.copyfile(copyFile, dst / copyFile)
        print("Copied: %s" % copyFile)

    writeFile(dst / "MANIFEST.in", (
        "include LICENSE.md\n"
        "include CREDITS.md\n"
        "recursive-include novelwriter/assets *\n"
    ))
    print("Wrote:  MANIFEST.in")

    if setupPy:
        writeFile(dst / "setup.py", (
            "import setuptools\n"
            "setuptools.setup()\n"
        ))
        print("Wrote:  setup.py")

    text = readFile(ROOT_DIR / "pyproject.toml")
    text = text.replace("setup/description_pypi.md", "data/description_short.txt")
    writeFile(dst / "pyproject.toml", text)
    print("Wrote:  pyproject.toml")

    return


##
#  Make Debian Package
##

def makeDebianPackage(
    signKey: str | None = None, sourceBuild: bool = False, distName: str = "unstable",
    buildName: str = "", forLaunchpad: bool = False
) -> str:
    """Build a Debian package."""
    print("")
    print("Build Debian Package")
    print("====================")
    print("On Debian/Ubuntu install: dh-python python3-all debhelper devscripts ")
    print("                          pybuild-plugin-pyproject")
    print("")

    # Version Info
    # ============

    numVers, hexVers, relDate = extractVersion()
    relDate = datetime.datetime.strptime(relDate, "%Y-%m-%d")
    pkgDate = email.utils.format_datetime(relDate.replace(hour=12, tzinfo=None))
    print("")

    if forLaunchpad:
        pkgVers = numVers.replace("a", "~a").replace("b", "~b").replace("rc", "~rc")
    else:
        pkgVers = numVers
    pkgVers = f"{pkgVers}+{buildName}" if buildName else pkgVers

    # Set Up Folder
    # =============

    bldDir = ROOT_DIR / "dist_deb"
    bldPkg = f"novelwriter_{pkgVers}"
    outDir = bldDir / bldPkg
    debDir = outDir / "debian"
    datDir = outDir / "data"

    bldDir.mkdir(exist_ok=True)
    if outDir.exists():
        print("Removing old build files ...")
        print("")
        shutil.rmtree(outDir)

    outDir.mkdir(exist_ok=False)

    # Check Additional Assets
    # =======================

    if not checkAssetsExist():
        print("ERROR: Missing build assets")
        sys.exit(1)

    # Copy novelWriter Source
    # =======================

    print("Copying novelWriter source ...")
    print("")

    copySourceCode(outDir)

    print("")
    print("Copying or generating additional files ...")
    print("")

    copyPackageFiles(outDir, setupPy=True)

    # Copy/Write Debian Files
    # =======================

    shutil.copytree(SETUP_DIR / "debian", debDir)
    print("Copied: debian/*")

    writeFile(debDir / "changelog", (
        f"novelwriter ({pkgVers}) {distName}; urgency=low\n\n"
        f"  * Update to version {pkgVers}\n\n"
        f" -- Veronica Berglyd Olsen <code@vkbo.net>  {pkgDate}\n"
    ))
    print("Wrote:  debian/changelog")

    # Copy/Write Data Files
    # =====================

    shutil.copytree(SETUP_DIR / "data", datDir)
    print("Copied: data/*")

    shutil.copyfile(SETUP_DIR / "description_short.txt", outDir / "data" / "description_short.txt")
    print("Copied: data/description_short.txt")

    # Build Package
    # =============

    print("")
    print("Running dpkg-buildpackage ...")
    print("")

    if signKey is None:
        signArgs = ["-us", "-uc"]
    else:
        signArgs = [f"-k{signKey}"]

    if sourceBuild:
        subprocess.call(["debuild", "-S"] + signArgs, cwd=outDir)
        toUpload(bldDir / f"{bldPkg}.tar.xz")
    else:
        subprocess.call(["dpkg-buildpackage"] + signArgs, cwd=outDir)
        shutil.copyfile(bldDir / f"{bldPkg}.tar.xz", bldDir / f"{bldPkg}.debian.tar.xz")
        toUpload(bldDir / f"{bldPkg}.debian.tar.xz")
        toUpload(bldDir / f"{bldPkg}_all.deb")
        toUpload(makeCheckSum(f"{bldPkg}.debian.tar.xz", cwd=bldDir))
        toUpload(makeCheckSum(f"{bldPkg}_all.deb", cwd=bldDir))

    print("")
    print("Done!")
    print("")

    if sourceBuild:
        ppaName = "novelwriter" if hexVers[-2] == "f" else "novelwriter-pre"
        return f"dput {ppaName}/{distName} {bldDir}/{bldPkg}_source.changes"

    return ""


##
#  Build Debian Package (build-deb)
##

def buildDebianPackage(args: argparse.Namespace) -> None:
    """Build a .deb package"""
    if not OS_LINUX:
        print("ERROR: Command 'build-deb' can only be used on Linux")
        sys.exit(1)
    signKey = SIGN_KEY if args.sign else None
    makeDebianPackage(signKey)
    return


##
#  Build Launchpad Packages (build-ubuntu)
##

def buildForLaunchpad(args: argparse.Namespace) -> None:
    """Wrapper for building Debian packages for Launchpad."""
    if not OS_LINUX:
        print("ERROR: Command 'build-ubuntu' can only be used on Linux")
        sys.exit(1)

    print("")
    print("Launchpad Packages")
    print("==================")
    print("")

    if args.build:
        bldNum = str(args.build)
    else:
        bldNum = "0"

    distLoop = [
        ("24.04", "noble"),
        ("24.10", "oracular"),
        ("25.04", "plucky"),
    ]

    print("Building Ubuntu packages for:")
    print("")
    for distNum, codeName in distLoop:
        print(f" * Ubuntu {distNum} {codeName.title()}")
    print("")

    signKey = SIGN_KEY if args.sign else None

    print(f"Sign Key: {str(signKey)}")
    print("")

    dputCmd = []
    for distNum, codeName in distLoop:
        buildName = f"ubuntu{distNum}.{bldNum}"
        dCmd = makeDebianPackage(
            signKey=signKey,
            sourceBuild=True,
            distName=codeName,
            buildName=buildName,
            forLaunchpad=True,
        )
        dputCmd.append(dCmd)

    print("Packages Built")
    print("==============")
    print("")
    for dCmd in dputCmd:
        print(f" > {dCmd}")
    print("")

    return


##
#  Build AppImage (build-appimage)
##

def buildAppImage(args: argparse.Namespace) -> None:
    """Build an AppImage."""
    try:
        import python_appimage  # noqa: F401 # type: ignore
    except ImportError:
        print(
            "ERROR: Package 'python-appimage' is missing on this system.\n"
            "       Please run 'pip install --user python-appimage' to install it.\n"
        )
        sys.exit(1)

    if not OS_LINUX:
        print("ERROR: Command 'build-ubuntu' can only be used on Linux")
        sys.exit(1)

    print("")
    print("Build AppImage")
    print("==============")
    print("")

    linuxTag = args.linux_tag
    pythonVer = args.python_version

    # Version Info
    # ============

    pkgVers, _, relDate = extractVersion()
    relDate = datetime.datetime.strptime(relDate, "%Y-%m-%d")
    print("")

    # Set Up Folder
    # =============

    bldDir = ROOT_DIR / "dist_appimage"
    bldPkg = f"novelwriter_{pkgVers}"
    outDir = bldDir / bldPkg
    imgDir = bldDir / "appimage"

    # Set Up Folders
    # ==============

    bldDir.mkdir(exist_ok=True)

    if outDir.exists():
        print("Removing old build files ...")
        print("")
        shutil.rmtree(outDir)

    outDir.mkdir()

    if imgDir.exists():
        print("Removing old build metadata files ...")
        print("")
        shutil.rmtree(imgDir)

    imgDir.mkdir()

    # Remove old AppImages
    if images := bldDir.glob("*.AppImage"):
        print("Removing old AppImages")
        print("")
        for image in images:
            image.unlink()

    # Copy novelWriter Source
    # =======================

    print("Copying novelWriter source ...")
    print("")

    copySourceCode(outDir)

    print("")
    print("Copying or generating additional files ...")
    print("")

    copyPackageFiles(outDir)

    # Write Metadata
    # ==============

    appDescription = readFile(SETUP_DIR / "description_short.txt")
    appdataXML = readFile(SETUP_DIR / "novelwriter.appdata.xml")
    appdataXML = appdataXML.format(description=appDescription)
    writeFile(imgDir / "novelwriter.appdata.xml", appdataXML)
    print("Wrote:  novelwriter.appdata.xml")

    writeFile(imgDir / "entrypoint.sh", (
        '#! /bin/bash \n'
        '{{ python-executable }} -sE ${APPDIR}/opt/python{{ python-version }}/bin/novelwriter "$@"'
    ))
    print("Wrote:  entrypoint.sh")

    writeFile(imgDir / "requirements.txt", str(outDir))
    print("Wrote:  requirements.txt")

    shutil.copyfile(SETUP_DIR / "data" / "novelwriter.desktop", imgDir / "novelwriter.desktop")
    print("Copied: novelwriter.desktop")

    shutil.copyfile(SETUP_DIR / "icons" / "novelwriter.svg", imgDir / "novelwriter.svg")
    print("Copied: novelwriter.svg")

    shutil.copyfile(
        SETUP_DIR / "data" / "hicolor" / "256x256" / "apps" / "novelwriter.png",
        imgDir / "novelwriter.png"
    )
    print("Copied: novelwriter.png")

    # Build AppImage
    # ==============

    try:
        subprocess.call([
            sys.executable, "-m", "python_appimage", "build", "app",
            "-l", linuxTag, "-p", pythonVer, "appimage"
        ], cwd=bldDir)
    except Exception as exc:
        print("AppImage build: FAILED")
        print("")
        print(str(exc))
        print("")
        sys.exit(1)

    bldFile = list(bldDir.glob("*.AppImage"))[0]
    outFile = bldDir / f"novelWriter-{pkgVers}.AppImage"
    bldFile.rename(outFile)
    shaFile = makeCheckSum(outFile.name, cwd=bldDir)

    toUpload(outFile)
    toUpload(shaFile)

    return


##
#  Generate MacOS PList
##

def genMacOSPlist(args: argparse.Namespace) -> None:
    """Set necessary values for .plist file for MacOS build."""
    outDir = SETUP_DIR / "macos"
    numVers = stripVersion(extractVersion()[0])
    copyrightYear = datetime.datetime.now().year

    # These keys are no longer used but are present for compatibility
    pkgVersMaj, pkgVersMin = numVers.split(".")[:2]

    plistXML = readFile(outDir / "Info.plist.template").format(
        macosBundleSVers=numVers,
        macosBundleVers=numVers,
        macosBundleVersMajor=pkgVersMaj,
        macosBundleVersMinor=pkgVersMin,
        macosBundleCopyright=f"Copyright 2018–{copyrightYear}, Veronica Berglyd Olsen",
    )

    print(f"Writing Info.plist to {outDir}/Info.plist")
    writeFile(outDir / "Info.plist", plistXML)

    return


# =============================================================================================== #
#  General Installers
# =============================================================================================== #

##
#  XDG Installation (xdg-install)
##

def xdgInstall(args: argparse.Namespace) -> None:
    """Will attempt to install icons and make a launcher."""
    print("")
    print("XDG Install")
    print("===========")
    print("")

    # Find Executable(s)
    # ==================

    exOpts = []

    testExec = shutil.which("novelWriter")
    if testExec is not None:
        exOpts.append(testExec)

    testExec = shutil.which("novelwriter")
    if testExec is not None:
        exOpts.append(testExec)

    testExec = ROOT_DIR / "novelWriter.py"
    if testExec.is_file():
        exOpts.append(str(testExec))

    useExec = ""
    nOpts = len(exOpts)
    if nOpts == 0:
        print("Error: No executables for novelWriter found.")
        sys.exit(1)
    elif nOpts == 1:
        useExec = exOpts[0]
    else:
        print("Found multiple novelWriter executables:")
        print("")
        for iExec, anExec in enumerate(exOpts):
            print(" [%d] %s" % (iExec, anExec))
        print("")
        intVal = int(input("Please select which novelWriter executable to use: "))
        print("")

        if intVal >= 0 and intVal < nOpts:
            useExec = exOpts[intVal]
        else:
            print("Error: Invalid selection.")
            sys.exit(1)

    print("Using executable: %s " % useExec)
    print("")

    # Create and Install Launcher
    # ===========================

    # Generate launcher
    desktopFile = ROOT_DIR / "novelwriter.desktop"
    desktopData = readFile(SETUP_DIR / "data" / "novelwriter.desktop")
    desktopData = desktopData.replace("Exec=novelwriter", f"Exec={useExec}")
    writeFile(desktopFile, desktopData)

    # Remove old desktop icon
    exCode = subprocess.call(
        ["xdg-desktop-icon", "uninstall", "novelwriter.desktop"]
    )

    # Install application launcher
    exCode = subprocess.call(
        ["xdg-desktop-menu", "install", "--novendor", "novelwriter.desktop"]
    )
    if exCode == 0:
        print("Installed menu launcher file")
    else:
        print(f"Error {exCode}: Could not install menu launcher file")

    # Install MimeType
    # ================

    exCode = subprocess.call([
        "xdg-mime", "install", "setup/data/x-novelwriter-project.xml"
    ])
    if exCode == 0:
        print("Installed mimetype")
    else:
        print(f"Error {exCode}: Could not install mimetype")

    # Install Icons
    # =============

    iconRoot = "setup/data/hicolor"
    sizeArr = ["16", "24", "32", "48", "64", "128", "256"]

    # App Icon
    for aSize in sizeArr:
        exCode = subprocess.call([
            "xdg-icon-resource", "install", "--novendor", "--noupdate",
            "--context", "apps", "--size", aSize,
            f"{iconRoot}/{aSize}x{aSize}/apps/novelwriter.png",
            "novelwriter"
        ])
        if exCode == 0:
            print(f"Installed app icon size {aSize}")
        else:
            print(f"Error {exCode}: Could not install app icon size {aSize}")

    # Mimetype
    for aSize in sizeArr:
        exCode = subprocess.call([
            "xdg-icon-resource", "install", "--noupdate",
            "--context", "mimetypes", "--size", aSize,
            f"{iconRoot}/{aSize}x{aSize}/mimetypes/application-x-novelwriter-project.png",
            "application-x-novelwriter-project"
        ])
        if exCode == 0:
            print(f"Installed mime icon size {aSize}")
        else:
            print(f"Error {exCode}: Could not install mime icon size {aSize}")

    # Update Cache
    exCode = subprocess.call(["xdg-icon-resource", "forceupdate"])
    if exCode == 0:
        print("Updated icon cache")
    else:
        print(f"Error {exCode}: Could not update icon cache")

    # Clean up
    desktopFile.unlink(missing_ok=True)

    print("")
    print("Done!")
    print("")

    return


##
#  XDG Uninstallation (xdg-uninstall)
##

def xdgUninstall(args: argparse.Namespace) -> None:
    """Will attempt to uninstall icons and the launcher."""
    print("")
    print("XDG Uninstall")
    print("=============")
    print("")

    # Application Menu Icon
    exCode = subprocess.call(
        ["xdg-desktop-menu", "uninstall", "novelwriter.desktop"]
    )
    if exCode == 0:
        print("Uninstalled menu launcher file")
    else:
        print(f"Error {exCode}: Could not uninstall menu launcher file")

    # Desktop Icon
    # (No longer installed)
    exCode = subprocess.call(
        ["xdg-desktop-icon", "uninstall", "novelwriter.desktop"]
    )
    if exCode == 0:
        print("Uninstalled desktop launcher file")
    else:
        print(f"Error {exCode}: Could not uninstall desktop launcher file")

    # Also include no longer used sizes
    sizeArr = ["16", "22", "24", "32", "48", "64", "96", "128", "256", "512"]

    # App Icons
    for aSize in sizeArr:
        exCode = subprocess.call([
            "xdg-icon-resource", "uninstall", "--noupdate",
            "--context", "apps", "--size", aSize, "novelwriter"
        ])
        if exCode == 0:
            print(f"Uninstalled app icon size {aSize}")
        else:
            print(f"Error {exCode}: Could not uninstall app icon size {aSize}")

    # Mimetype
    for aSize in sizeArr:
        exCode = subprocess.call([
            "xdg-icon-resource", "uninstall", "--noupdate",
            "--context", "mimetypes", "--size", aSize,
            "application-x-novelwriter-project"
        ])
        if exCode == 0:
            print(f"Uninstalled mime icon size {aSize}")
        else:
            print(f"Error {exCode}: Could not uninstall mime icon size {aSize}")

    # Update Cache
    exCode = subprocess.call(["xdg-icon-resource", "forceupdate"])
    if exCode == 0:
        print("Updated icon cache")
    else:
        print(f"Error {exCode}: Could not update icon cache")

    print("")
    print("Done!")
    print("")

    return


# =============================================================================================== #
#  Process Command Line
# =============================================================================================== #

if __name__ == "__main__":
    """Parse command line options and run the commands."""
    parser = argparse.ArgumentParser(
        usage="pkgutils.py [command] [--flags]",
        description=(
            "This tool provides setup and build commands for installing or distibuting "
            "novelWriter as a package on Linux, Mac and Windows, as well as developer tools "
            "for internationalisation."
        )
    )
    parsers = parser.add_subparsers()

    # Version
    cmdVersion = parsers.add_parser(
        "version", help="Print the novelWriter version."
    )
    cmdVersion.set_defaults(func=printVersion)

    # General
    # =======

    # Pip Install
    cmdPipInstall = parsers.add_parser(
        "pip", help="Install all package dependencies for novelWriter using pip."
    )
    cmdPipInstall.add_argument("--linux", action="store_true", help="For Linux.", default=OS_LINUX)
    cmdPipInstall.add_argument("--mac", action="store_true", help="For MacOS.", default=OS_DARWIN)
    cmdPipInstall.add_argument("--win", action="store_true", help="For Windows.", default=OS_WIN)
    cmdPipInstall.set_defaults(func=installPackages)

    # Additional Builds
    # =================

    # Build Icons
    cmdIcons = parsers.add_parser(
        "icons", help="Build icon theme files from source."
    )
    cmdIcons.add_argument("--sources", help="Working directory for sources.")
    cmdIcons.add_argument("--style", help="What icon style to build.")
    cmdIcons.set_defaults(func=utils.icon_themes.main)

    # Import Translations
    cmdImportTS = parsers.add_parser(
        "qtlimport", help="Import updated i18n files from a Crowdin zip file."
    )
    cmdImportTS.add_argument("file", help="Path to zip file from Crowdin")
    cmdImportTS.set_defaults(func=importI18nUpdates)

    # Update i18n Sources
    cmdUpdateTS = parsers.add_parser(
        "qtlupdate", help=(
            "Update translation files for internationalisation. "
            "The files to be updated must be provided as arguments. "
            "New files can be created by giving a 'nw_<lang>.ts' file name "
            "where <lang> is a valid language code."
        )
    )
    cmdUpdateTS.add_argument("files", nargs="+")
    cmdUpdateTS.set_defaults(func=updateTranslationSources)

    # Build i18n Files
    cmdBuildQM = parsers.add_parser(
        "qtlrelease", help="Build the language files for internationalisation."
    )
    cmdBuildQM.set_defaults(func=buildTranslationAssets)

    # Build Manual
    cmdBuildManual = parsers.add_parser(
        "manual", help="Build the help documentation as a PDF (requires LaTeX)."
    )
    cmdBuildManual.set_defaults(func=buildPdfManual)

    # Build Sample
    cmdBuildSample = parsers.add_parser(
        "sample", help="Build the sample project zip file and add it to assets."
    )
    cmdBuildSample.set_defaults(func=buildSampleZip)

    # Clean Assets
    cmdCleanAssets = parsers.add_parser(
        "clean-assets", help="Delete assets built by manual, sample and qtlrelease."
    )
    cmdCleanAssets.set_defaults(func=cleanBuiltAssets)

    # Build Assets
    cmdBuildAssets = parsers.add_parser(
        "build-assets", help="Build all assets. Includes manual, sample and qtlrelease."
    )
    cmdBuildAssets.set_defaults(func=buildAllAssets)

    # Python Packaging
    # ================

    # Build Debian Package
    cmdBuildDeb = parsers.add_parser(
        "build-deb", help=(
            "Build a .deb package for Debian and Ubuntu. "
            "Add --sign to sign package."
        )
    )
    cmdBuildDeb.add_argument("--sign", action="store_true", help="Sign the package.")
    cmdBuildDeb.set_defaults(func=buildDebianPackage)

    # Build Ubuntu Packages
    cmdBuildUbuntu = parsers.add_parser(
        "build-ubuntu", help=(
            "Build a .deb package for Debian and Ubuntu. "
            "Add --sign to sign package. "
            "Add --first to set build number to 0."
        )
    )
    cmdBuildUbuntu.add_argument("--sign", action="store_true", help="Sign the package.")
    cmdBuildUbuntu.add_argument("--build", type=int, help="Set build number.")
    cmdBuildUbuntu.set_defaults(func=buildForLaunchpad)

    # Build AppImage
    cmdBuildAppImage = parsers.add_parser(
        "build-appimage", help=(
            "Build an AppImage. "
            "Argument --linux-tag defaults manylinux_2_28_x86_64, and --python-version to 3.11."
        )
    )
    cmdBuildAppImage.add_argument(
        "--linux-tag",
        default="manylinux_2_28_x86_64",
        help=(
            "Linux compatibility tag (e.g. manylinux_2_28_x86_64) "
            "see https://python-appimage.readthedocs.io/en/latest/#available-python-appimages "
            "and https://github.com/pypa/manylinux for a list of valid tags."
        ),
    )
    cmdBuildAppImage.add_argument(
        "--python-version", default="3.11", help="Python version (e.g. 3.11)"
    )
    cmdBuildAppImage.set_defaults(func=buildAppImage)

    # Build Windows Inno Setup Installer
    cmdBuildSetupExe = parsers.add_parser(
        "build-win-exe", help="Build a setup.exe file with Python embedded for Windows."
    )
    cmdBuildSetupExe.set_defaults(func=utils.windows_build.main)

    # Build Binary
    cmdBuildBinary = parsers.add_parser(
        "build-bin", help="Build a standalone binary package."
    )
    cmdBuildBinary.set_defaults(func=utils.binary_dist.main)

    # Build Clean
    cmdBuildClean = parsers.add_parser(
        "build-clean", help="Recursively delete all build folders."
    )
    cmdBuildClean.set_defaults(func=cleanBuildDirs)

    # Generate MacOS PList File
    cmdBuildMacOSPlist = parsers.add_parser(
        "gen-plist", help="Generate an Info.plist for use in a MacOS Bundle."
    )
    cmdBuildMacOSPlist.set_defaults(func=genMacOSPlist)

    # General Installers
    # ==================

    # Linux XDG Install
    cmdXDGInstall = parsers.add_parser(
        "xdg-install", help=(
            "Install launcher and icons for freedesktop systems. Run as root or with sudo for "
            "system-wide install, or as user for single user install."
        )
    )
    cmdXDGInstall.set_defaults(func=xdgInstall)

    # Linux XDG Uninstall
    cmdXDGUninstall = parsers.add_parser(
        "xdg-uninstall", help=(
            "Remove the launcher and icons for the current system "
            "as installed by the 'xdg-install' command."
        )
    )
    cmdXDGUninstall.set_defaults(func=xdgUninstall)

    args = parser.parse_args()
    args.func(args)
