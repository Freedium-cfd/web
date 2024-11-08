FROM golang:1.23.1-alpine3.20 AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . ./

RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /main ./main.go

FROM alpine:3.20
WORKDIR /app

COPY --from=builder /main .

ENTRYPOINT ["/app/main"]
