package cmd

import "fmt"

func rollback(args []string) error {
	if isWindows() {
		return fmt.Errorf("mochi rollback is a mochios-only command (no windows equivalent)")
	}
	if !hasAbroot() {
		return fmt.Errorf("abroot not available on this system")
	}
	fmt.Println("rolling back...")
	return runAbroot("rollback")
}
