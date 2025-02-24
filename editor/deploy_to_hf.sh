HF_REPO=/tmp/hf-croissant
echo "Deleting $HF_REPO..."
rm -rf ${HF_REPO}
git clone git@hf.co:spaces/marcenacp/croissant-editor ${HF_REPO}
streamlit_version_in_hf=$(grep -oP 'sdk_version: \K[0-9]+\.[0-9]+\.[0-9]+' ${HF_REPO}/README.md)
streamlit_version_in_gh=$(grep -oP 'streamlit\=\=\K[0-9]+\.[0-9]+\.[0-9]+' requirements.txt)
if [ "$streamlit_version_in_hf" != "$streamlit_version_in_gh" ]; then
  echo "ERROR: Versions of Streamlit in the requirements.txt and ${HF_REPO}/README.md should be the same."
  exit 1
fi
echo "Copying files from $PWD to $HF_REPO..."
rsync -aP --exclude="README.md" --exclude="*node_modules*" --exclude="cypress/*" --exclude="*__pycache__*" . ${HF_REPO}
cd ${HF_REPO}
git add .
git commit -m "Deploy (see actual commits on https://github.com/mlcommons/croissant)."
echo "Now push with: 'cd $HF_REPO && git push'."
echo "Warning: if it fails, you may need to follow https://huggingface.co/docs/hub/security-git-ssh#generating-a-new-ssh-keypair"
echo "On Hugging Face Spaces, you might have to set the following environment variables:"
echo "- REDIRECT_URI"
echo "- OAUTH_STATE"
echo "- OAUTH_CLIENT_ID"
echo "- OAUTH_CLIENT_SECRET"
echo "Visit: https://huggingface.co/spaces/marcenacp/croissant-editor"
