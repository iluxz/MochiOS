package cmd

import "fmt"

func snapshot(args []string) error {
	if isWindows() {
		return fmt.Errorf("mochi snapshot is a mochios-only command (no windows equivalent)")
	}
	if !hasAbroot() {
		return fmt.Errorf("abroot not available on this system")
	}
	return runAbroot("snapshot")
}
