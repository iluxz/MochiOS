package cmd

import "fmt"

func snapshot(args []string) error {
	if !hasAbroot() {
		return fmt.Errorf("abroot not available on this system")
	}
	return runAbroot("snapshot")
}
