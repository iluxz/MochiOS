package cmd

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
)

const updateURL = "https://raw.githubusercontent.com/iluxz/MochiOS/main/mochi/mochi.exe"

func selfUpdate(args []string) error {
	fmt.Print("checking for updates... ")

	exe, err := os.Executable()
	if err != nil {
		return fmt.Errorf("cant find self: %w", err)
	}

	tmp, err := os.CreateTemp("", "mochi-*.exe")
	if err != nil {
		return fmt.Errorf("cant create temp: %w", err)
	}
	tmpPath := tmp.Name()

	resp, err := http.Get(updateURL)
	if err != nil {
		tmp.Close()
		os.Remove(tmpPath)
		return fmt.Errorf("download failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		tmp.Close()
		os.Remove(tmpPath)
		return fmt.Errorf("download failed: http %d", resp.StatusCode)
	}

	_, err = io.Copy(tmp, resp.Body)
	tmp.Close()
	if err != nil {
		os.Remove(tmpPath)
		return fmt.Errorf("download failed: %w", err)
	}

	fmt.Println("downloaded, replacing...")

	if runtime.GOOS == "windows" {
		return replaceWindows(exe, tmpPath)
	}
	return replaceUnix(exe, tmpPath)
}

func replaceWindows(exe, tmp string) error {
	// Can't replace a running exe on windows, so spawn a .bat that waits
	// then replaces and cleans up
	bat := filepath.Join(os.TempDir(), "mochi-update.bat")
	batContent := fmt.Sprintf(`@echo off
:sleep
timeout /t 1 /nobreak >nul 2>&1
if exist "%s" (
  del "%s"
  if exist "%s" goto sleep
)
copy /y "%s" "%s" >nul
del "%s"
`, exe, exe, exe, tmp, exe, tmp)
	os.WriteFile(bat, []byte(batContent), 0755)
	return fmt.Errorf("replacement queued — mochi-update.bat in temp dir, run it manually or reboot")
}

func replaceUnix(exe, tmp string) error {
	err := os.Rename(tmp, exe)
	if err != nil {
		os.Remove(tmp)
		return fmt.Errorf("replace failed: %w", err)
	}
	os.Chmod(exe, 0755)
	return nil
}
