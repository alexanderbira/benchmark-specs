# Need to use amd for the older version of Haskell
FROM --platform=linux/amd64 haskell:8.6.5

# Install git
RUN apt-get install -y git

# Clone the Syfco repo
RUN git clone https://github.com/reactive-systems/syfco.git

# Build Syfco
WORKDIR /syfco

RUN cabal update
# Old dependency needs to be manually installed
RUN cabal install convertible-1.1.1.0
RUN cabal build

# Add Syfco to the path
ENV PATH="/syfco/dist/build/syfco:${PATH}"

# Work in /data, since we'll use it as the mount point for our volume
WORKDIR /data

# Syfco will be the entrypoint for the container to simplify things
ENTRYPOINT ["syfco"]