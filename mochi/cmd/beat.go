package cmd

import "fmt"

func beat(args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("usage: mochi beat <package>...")
	}

	if isWindows() {
		for _, pkg := range args {
			fmt.Printf("beating %s... ", pkg)
		}
		wingetArgs := append([]string{"install", "--disable-interactivity", "--accept-package-agreements", "--accept-source-agreements"}, args...)
		err := runWinget(wingetArgs...)
		if err != nil {
			fmt.Println("failed")
			return err
		}
		fmt.Println("done!")
		return nil
	}

	for _, pkg := range args {
		fmt.Printf("beating %s...\n", pkg)
	}
	return runPacman(append([]string{"-S", "--needed"}, args...)...)
}
