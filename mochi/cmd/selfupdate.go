package cmd

import (
	"crypto/sha256"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"strings"
)

const baseURL = "https://raw.githubusercontent.com/iluxz/MochiOS/main/mochi/"

func updateURLForPlatform() string {
	if runtime.GOOS == "windows" {
		return baseURL + "mochi.exe"
	}
	return baseURL + "mochi"
}

func checksumURLForPlatform() string {
	if runtime.GOOS == "windows" {
		return baseURL + "mochi.exe.sha256"
	}
	return baseURL + "mochi.sha256"
}

func downloadAndVerify(url string, tmp *os.File) error {
	resp, err := http.Get(url)
	if err != nil {
		return fmt.Errorf("download failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("download failed: http %d\nurl: %s\n%s", resp.StatusCode, resp.Request.URL.String(), string(body))
	}

	h := sha256.New()
	if _, err := io.Copy(io.MultiWriter(tmp, h), resp.Body); err != nil {
		return fmt.Errorf("download failed: %w", err)
	}
	actual := fmt.Sprintf("%x", h.Sum(nil))

	// fetch expected checksum
	csResp, err := http.Get(checksumURLForPlatform())
	if err != nil {
		fmt.Printf("warning: could not fetch checksum (%v), skipping verification\n", err)
		return nil
	}
	defer csResp.Body.Close()

	if csResp.StatusCode != 200 {
		fmt.Printf("warning: checksum file returned http %d, skipping verification\n", csResp.StatusCode)
		return nil
	}

	csBody, _ := io.ReadAll(csResp.Body)
	expected := strings.TrimSpace(string(csBody))

	// checksum file may contain "hash  filename" or just "hash"
	if parts := strings.Fields(expected); len(parts) >= 1 {
		expected = parts[0]
	}

	if actual != expected {
		os.Remove(tmp.Name())
		return fmt.Errorf("checksum mismatch!\nexpected: %s\nactual:   %s", expected, actual)
	}

	return nil
}

func selfUpdate(args []string) error {
	fmt.Print("checking for updates... ")

	exe, err := os.Executable()
	if err != nil {
		return fmt.Errorf("cant find self: %w", err)
	}

	tmpName := "mochi-update-*"
	if runtime.GOOS == "windows" {
		tmpName = "mochi-*.exe"
	}
	tmp, err := os.CreateTemp("", tmpName)
	if err != nil {
		return fmt.Errorf("cant create temp: %w", err)
	}
	tmpPath := tmp.Name()

	if err := downloadAndVerify(updateURLForPlatform(), tmp); err != nil {
		tmp.Close()
		os.Remove(tmpPath)
		return err
	}
	tmp.Close()

	fmt.Println("downloaded, replacing...")

	if runtime.GOOS == "windows" {
		replaceWindows(exe, tmpPath)
		return nil
	}
	return replaceUnix(exe, tmpPath)
}

func replaceWindows(exe, tmp string) {
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
	if err := os.WriteFile(bat, []byte(batContent), 0755); err != nil {
		fmt.Printf("warning: could not create update script: %v\n", err)
	} else {
		fmt.Printf("done! run %s or reboot to finish the update\n", bat)
	}
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
