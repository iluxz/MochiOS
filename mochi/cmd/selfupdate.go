package cmd

import (
	"crypto/sha256"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
)

const baseURL = "https://github.com/iluxz/MochiOS/raw/gh-pages/static/"

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
	// rename current exe to .old, copy new one in place, then delete .old
	// Windows allows renaming a running exe but not deleting it
	old := exe + ".old"
	os.Remove(old) // clean up any previous .old
	if err := os.Rename(exe, old); err != nil {
		fmt.Printf("warning: could not rename current exe: %v\n", err)
		fmt.Printf("run this manually: copy /y \"%s\" \"%s\"\n", tmp, exe)
		return
	}
	if err := copyFile(tmp, exe); err != nil {
		fmt.Printf("warning: could not copy new exe: %v\n", err)
		os.Rename(old, exe) // restore
		return
	}
	// schedule .old cleanup via a bat that waits briefly then deletes
	bat := filepath.Join(os.TempDir(), "mochi-cleanup-old.bat")
	batContent := fmt.Sprintf(`@echo off
timeout /t 2 /nobreak >nul 2>&1
del "%s"
del "%%~f0"
`, old)
	os.WriteFile(bat, []byte(batContent), 0755)
	// run the cleanup bat in background
	exec.Command("cmd", "/c", "start", "/b", bat).Start()
	fmt.Println("done! restart mochi to use the new version")
}

func copyFile(src, dst string) error {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()
	out, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer out.Close()
	_, err = io.Copy(out, in)
	return err
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
