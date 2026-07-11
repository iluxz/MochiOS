package cmd

import "fmt"

func remove(args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("usage: mochi remove <package>...")
	}
	for _, pkg := range args {
		fmt.Printf("removing %s...\n", pkg)
	}
	return runPacmanInteractive(append([]string{"-R"}, args...)...)
}
