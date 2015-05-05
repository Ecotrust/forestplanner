all:
	pandoc -N \
	--template=doc_template.tex \
	--toc \
	--latex-engine=xelatex \
	--variable=geometry:margin=1.2in \
	--variable monofont="Liberation Mono" \
	--variable sansfont="Liberation Sans" \
	--variable mainfont="Liberation Serif" \
	--variable fontsize=12pt \
	user_inventory.md -o user_inventory.pdf
