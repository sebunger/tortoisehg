#!/bin/zsh

set -euo pipefail

unmount_DEVICE () {
    [ -n "${DEVICE-}" ] && hdiutil detach "${DEVICE}"
}

DMG_BACKGROUND_IMG="background.png"

# you should not need to change these
APP_EXE="${APP_NAME}.app/Contents/MacOS/${APP_NAME}"

VOL_NAME="${APP_NAME}-${THG_VERSION}"
DMG_TMP="releases/${VOL_NAME}-temp.dmg"
DMG_FINAL="releases/${VOL_NAME}-mac-x64-${QT_VERSION}.dmg"
STAGING_DIR="./dist"

rm -f "${STAGING_DIR}"/.DS_Store
mkdir -p releases

# figure out how big our DMG needs to be
#  assumes our contents are at least 1M!
SIZE=`du -sh "${STAGING_DIR}" | sed 's/\([0-9]*\)M\(.*\)/\1/'`
SIZE=`echo "${SIZE} + 2.0" | bc | awk '{print int($1+0.5)}'`

if [ $? -ne 0 ]; then
   echo "Error: Cannot compute size of staging dir"
   exit
fi

echo "Volume Size: ${SIZE}M"

rm -f "${DMG_TMP}"

# create the temp DMG file
hdiutil create -srcfolder "${STAGING_DIR}" -volname "${VOL_NAME}" -fs HFS+ \
      -fsargs "-c c=64,a=16,e=16" -format UDRW -size ${SIZE}M "${DMG_TMP}"

echo "Created DMG: ${DMG_TMP}"

# mount it and save the device
trap unmount_DEVICE EXIT
DEVICE=$(hdiutil attach -readwrite -noverify "${DMG_TMP}" | \
         egrep '^/dev/' | sed 1q | awk '{print $1}')

sleep 5

# add a link to the Applications dir
echo "Add link to /Applications"
pushd /Volumes/"${VOL_NAME}"
ln -f -s /Applications
popd

# add a background image
mkdir /Volumes/"${VOL_NAME}"/.background
cp "${DMG_BACKGROUND_IMG}" /Volumes/"${VOL_NAME}"/.background/

# tell the Finder to resize the window, set the background,
#  change the icon size, place the icons in the right position, etc.
echo '
   tell application "Finder"
     tell disk "'${VOL_NAME}'"
           open
           set current view of container window to icon view
           set toolbar visible of container window to false
           set statusbar visible of container window to false
           set the bounds of container window to {400, 100, 1040, 580}
           set viewOptions to the icon view options of container window
           set arrangement of viewOptions to not arranged
           set icon size of viewOptions to 160
           set background picture of viewOptions to file ".background:'${DMG_BACKGROUND_IMG}'"
           set position of item "'${APP_NAME}'.app" of container window to {135, 285}
           set position of item "Applications" of container window to {510, 285}
           close
           open
           update without registering applications
           delay 3

           set dsStore to "\"" & "/Volumes/" & "'${VOL_NAME}'" & "/" & ".DS_STORE\""
           set waitTime to 0
           set ejectMe to false
           repeat while ejectMe is false
               delay 1
               set waitTime to waitTime + 1

               if (do shell script "[ -f " & dsStore & " ]; echo $?") = "0" then set ejectMe to true
           end repeat
           log "waited " & waitTime & " seconds for .DS_STORE to be created."
           close
     end tell
   end tell
' | osascript

chmod -Rf go-w /Volumes/"${VOL_NAME}"
sync

# unmount it
hdiutil detach "${DEVICE}"
trap - EXIT

# now make the final image a compressed disk image
echo "Creating compressed image"
rm -rf "${DMG_FINAL}"
hdiutil convert "${DMG_TMP}" -format UDZO -imagekey zlib-level=9 -o "${DMG_FINAL}"

# clean up
rm -rf "${DMG_TMP}"
#rm -rf "${STAGING_DIR}"

# Requires 10.11.5 or later
if [ -n "${CODE_SIGN_IDENTITY:-}" ]; then
  echo "Signing disk image"
  codesign -s "${CODE_SIGN_IDENTITY}" --timestamp ${DMG_FINAL}
fi

echo 'Done.'
