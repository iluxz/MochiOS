package cmd

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
	"strings"
)

var wingetOK = []string{
	"already installed",
	"no available upgrade",
	"no newer package",
}

var wingetNoise = []string{
	"microsoft",
	"license",
	"terms",
	"eula",
	"third.party",
}

func runWinget(args ...string) error {
	c := exec.Command("winget", args...)
	var outBuf, errBuf bytes.Buffer
	c.Stdout = &outBuf
	c.Stderr = &errBuf
	c.Stdin = os.Stdin

	err := c.Run()
	output := strings.ToLower(outBuf.String() + "\n" + errBuf.String())

	if err != nil {
		for _, ok := range wingetOK {
			if strings.Contains(output, ok) {
				return nil
			}
		}
	}

	if err != nil {
		msg := cleanWingetMsg(outBuf.String(), errBuf.String())
		return fmt.Errorf("winget error: %s", msg)
	}

	return nil
}

func cleanWingetMsg(stdout, stderr string) string {
	lines := strings.Split(strings.TrimSpace(stdout+"\n"+stderr), "\n")
	var clean []string
	for _, line := range lines {
		lower := strings.ToLower(line)
		skip := false
		for _, n := range wingetNoise {
			if strings.Contains(lower, n) {
				skip = true
				break
			}
		}
		if !skip && strings.TrimSpace(line) != "" {
			clean = append(clean, strings.TrimSpace(line))
		}
	}
	if len(clean) == 0 {
		return "operation failed"
	}
	return strings.Join(clean, "; ")
}
