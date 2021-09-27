module.exports = {
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
      