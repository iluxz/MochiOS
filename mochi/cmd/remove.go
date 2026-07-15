package cmd

import "fmt"

func remove(args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("usage: mochi remove <package>...")
	}

	if isWindows() {
		for _, pkg := range args {
			fmt.Printf("removing %s... ", pkg)
		}
		err := runWinget(append([]string{"uninstall", "--disable-interactivity"}, args...)...)
		if err != nil {
			fmt.Println("failed")
			return err
		}
		fmt.Println("done!")
		return nil
	}

	for _, pkg := range args {
		fmt.Printf("removing %s...\n", pkg)
	}
	return runPacmanInteractive(append([]string{"-R"}, args...)...)
}
