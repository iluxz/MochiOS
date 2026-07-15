package cmd

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
)

var subcommands = []string{
	"beat", "install",
	"remove", "uninstall", "rm",
	"update", "upgrade",
	"search",
	"status",
	"deploy",
	"rollback",
	"snapshot",
	"run",
	"help",
}

func isWindows() bool {
	return runtime.GOOS == "windows"
}

func Execute() error {
	exe := strings.TrimSuffix(strings.ToLower(filepath.Base(os.Args[0])), ".exe")
	if exe != "mochi" {
		for _, sc := range subcommands {
			if exe == sc {
				fmt.Fprintf(os.Stderr, "🍡 use 'mochi %s' instead!\n", sc)
				os.Args = append([]string{os.Args[0], sc}, os.Args[1:]...)
				break
			}
		}
	}

	if len(os.Args) < 2 {
		printUsage()
		return nil
	}

	cmd := os.Args[1]
	args := os.Args[2:]

	switch cmd {
	case "beat", "install":
		return beat(args)
	case "remove", "uninstall", "rm":
		return remove(args)
	case "update", "upgrade":
		return updateCmd(args)
	case "search":
		return search(args)
	case "status":
		return statusCmd(args)
	case "deploy":
		return deploy(args)
	case "rollback":
		return rollback(args)
	case "snapshot":
		return snapshot(args)
	case "run":
		return runFile(args)
	case "help", "--help", "-h":
		printUsage()
		return nil
	default:
		return fmt.Errorf("unknown command: %s", cmd)
	}
}

func printUsage() {
	fmt.Println(`mochi - the mochios package manager (windows/mochios)

usage:
  mochi beat <pkg>     install a package (also: mochi install)
  mochi remove <pkg>   remove a package
  mochi update         atomic update or winget upgrade --all
  mochi search <q>     search for a package
  mochi status         show system status
  mochi deploy <pkgs>  mochios only: deploy to inactive root
  mochi rollback       mochios only: rollback snapshot
  mochi snapshot       mochios only: list snapshots
  mochi run <file>     run scripts in any supported language
  mochi help           show this help`)
}

func runAbroot(args ...string) error {
	return run("abroot", args...)
}

func hasAbroot() bool {
	_, err := exec.LookPath("abroot")
	return err == nil
}

func runPacman(args ...string) error {
	return run("pacman", append([]string{"--noconfirm"}, args...)...)
}

func runPacmanInteractive(args ...string) error {
	return run("pacman", args...)
}

func run(name string, args ...string) error {
	c := exec.Command(name, args...)
	c.Stdout = os.Stdout
	c.Stderr = os.Stderr
	c.Stdin = os.Stdin
	return c.Run()
}
