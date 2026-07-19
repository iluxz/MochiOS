package cmd

import (
	"fmt"
	"os"
	"os/exec"
)

const mochiRepoBlock = "\n[mochi]\nServer = https://github.com/iluxz/MochiOS/raw/gh-pages/repo/os/x86_64\nSigLevel = Optional TrustAll\n"

func repo(args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("usage: mochi repo <subcommand> [args...]\n\nsubcommands:\n  add    add the mochi package repo to pacman.conf")
	}
	switch args[0] {
	case "add":
		return repoAdd(args[1:])
	default:
		return fmt.Errorf("unknown repo command: %s", args[0])
	}
}

func repoAdd(args []string) error {
	if isWindows() {
		return fmt.Errorf("repo command is not supported on windows")
	}

	// check if already added
	pacmanConf := "/etc/pacman.conf"
	data, err := os.ReadFile(pacmanConf)
	if err != nil {
		return fmt.Errorf("reading pacman.conf: %w", err)
	}
	if containsRepoBlock(string(data), "[mochi]") {
		fmt.Println("mochi repo already in pacman.conf")
		return nil
	}

	// backup
	backup := pacmanConf + ".bak"
	if err := os.Rename(pacmanConf, backup); err != nil {
		return fmt.Errorf("backing up pacman.conf: %w", err)
	}

	// append repo block
	f, err := os.Create(pacmanConf)
	if err != nil {
		os.Rename(backup, pacmanConf)
		return fmt.Errorf("writing pacman.conf: %w", err)
	}
	defer f.Close()

	if _, err := f.Write(data); err != nil {
		os.Rename(backup, pacmanConf)
		return fmt.Errorf("writing pacman.conf: %w", err)
	}
	if _, err := f.WriteString(mochiRepoBlock); err != nil {
		os.Rename(backup, pacmanConf)
		return fmt.Errorf("writing mochi repo: %w", err)
	}

	fmt.Println("added mochi repo to pacman.conf (SigLevel: Optional TrustAll)")

	// refresh
	if pacman, err := exec.LookPath("pacman"); err == nil {
		fmt.Println("refreshing package list...")
		_ = run(pacman, "-Sy")
	}

	return nil
}

func containsRepoBlock(s, marker string) bool {
	for i := 0; i <= len(s)-len(marker); i++ {
		if s[i] == '[' && i+len(marker) <= len(s) && s[i:i+len(marker)] == marker {
			return true
		}
	}
	return false
}
