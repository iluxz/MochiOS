package cmd

import "fmt"

func rollback(args []string) error {
	if !hasAbroot() {
		return fmt.Errorf("abroot not available on this system")
	}
	fmt.Println("rolling back...")
	return runAbroot("rollback")
}
