package cmd

import "fmt"

func beat(args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("usage: mochi beat <package>...")
	}
	for _, pkg := range args {
		fmt.Printf("\U0001f361 beating %s...\n", pkg)
	}
	return runPacman(append([]string{"-S", "--needed"}, args...)...)
}
