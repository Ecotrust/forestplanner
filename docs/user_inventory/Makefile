all:
	pandoc -N \
	--template=doc_template.tex \
	--toc \
	--latex-engine=xelatex \
	--variable monofont="Liberation Mono" \
	--variable mainfont="Georgia" \
	--variable sansfont="Liberation Sans" \
	--variable fontsize=12pt \
	user_inventory.md -o user_inventory.pdf
