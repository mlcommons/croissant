HF_REPO=/tmp/hf-croissant
echo "Deleting $HF_REPO..."
rm -rf ${HF_REPO}
git clone git@hf.co:spaces/marcenacp/croissant-editor ${HF_REPO}
echo "Copying files from $PWD to $HF_REPO..."
rsync -aP --exclude="README.md" --exclude="*node_modules*" --exclude="*__pycache__*" . ${HF_REPO}
cd ${HF_REPO}
echo "Now push with: 'cd $HF_REPO && git add && git commit && git push'."
echo "Warning: if it fails, you may need to follow https://huggingface.co/docs/hub/security-git-ssh#generating-a-new-ssh-keypair"
echo "On Hugging Face Spaces, you might have to set the following environment variables:"
echo "- REDIRECT_URI"
echo "- OAUTH_STATE"
echo "- OAUTH_CLIENT_ID"
echo "- OAUTH_CLIENT_SECRET"
