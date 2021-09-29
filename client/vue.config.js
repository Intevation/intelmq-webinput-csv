module.exports = {
  publicPath: '/', //Adjust path prefix for deployment here to have all static files requested with this perefix.
  lintOnSave: "error",
  devServer: {
    disableHostCheck: true,
    proxy: {
      "/api": {
        target: "http://localhost:8002"
      }
    }
  }
};
      