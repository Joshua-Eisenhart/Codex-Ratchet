// verdict depends on trial number, not the artifact — high-entropy judge
process.exit(Number(process.argv[3]) % 2);
