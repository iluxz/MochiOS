package cmd

import (
	"fmt"
	"os"
	"os/exec"
)

func Execute() error {
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
	case "help", "--help", "-h":
		printUsage()
		return nil
	default:
		return fmt.Errorf("unknown command: %s", cmd)
	}
}

func printUsage() {
	fmt.Println(`mochi - the mochios package manager

usage:
  mochi beat <pkg>     install a package (also: mochi install)
  mochi remove <pkg>   remove a package
  mochi update         atomic update (abroot deploy)
  mochi search <q>     search for a package
  mochi status         show abroot partition status
  mochi deploy <pkgs>  deploy update to inactive root
  mochi rollback       rollback to previous snapshot
  mochi snapshot       list snapshots
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
