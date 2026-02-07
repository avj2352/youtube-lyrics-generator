aider:
	@echo "Launching Aider CLI (Bedrock - Sonnet)🚀"
	# aider --model bedrock/claude-sonnet-4-5-20250929-v1:0
	aider --model bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0

tree:
	@echo "Show project structure..."
	tree -L 5 -I __pycache__ -I .venv

clean:
	@echo "Cleanup dependencies..."
	rm -rf __pycache__/
	rm -rf .venv
	rm -f uv.lock
	rm -rf download
	mkdir download
