setwd("C:\\projects\\murdock\\GNN\\databases\\")
#origdata <- read.csv('sppz_all.csv')
d <- subset(origdata, IMAP_DOMSPP == 'PICO      ' )
dm <- na.omit(cbind(d$QMDA_DOM, d$AGE_DOM,d$SDI_REINEKE, d$TREER,  d$DDI, d$OGSI, d$SC, d$STNDHGT))
#dm <- scale(dm)
colnames(dm) <- c("diam", "age",  "sdi", "rich", "ddi", "ogsi", "sc", "standhgt")

# k-means
#dm.fit <- kmeans(dm, 10, iter.max=20, nstart=25)
#plot(ddi ~ sdi, data=dm, col=dm.fit$cluster, pch=16)
#library(rgl)
#plot3d(dm, col=dm.fit$cluster, type="s", size=0.5)
#print(dm.fit)


# Ward Hierarchical Clustering
#dm.dist <- dist(dm, method = "euclidean") # distance matrix
#dm.hier.fit <- hclust(dm.dist, method="ward") 
#plot(dm.hier.fit) # display dendogram
#groups <- cutree(dm.hier.fit, k=5) # cut tree into 5 clusters
# draw dendogram with red borders around the 5 clusters 
#rect.hclust(dm.hier.fit, k=5, border="red")

# Model Based Clustering
library(mclust)
dm.mclust.fit <- Mclust(dm)
plot(dm.mclust.fit, dm) # plot results 
print(dm.mclust.fit) # display the best model