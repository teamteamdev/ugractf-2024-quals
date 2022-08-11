FROM mcr.microsoft.com/dotnet/aspnet:8.0.1-bookworm-slim-amd64 AS base
WORKDIR /app

ENV ASPNETCORE_ENVIRONMENT Production

FROM mcr.microsoft.com/dotnet/sdk:8.0.101-bookworm-slim-amd64 AS build
WORKDIR /src
COPY ["./pastapp.csproj", "/src"]
RUN dotnet restore "pastapp.csproj"
COPY . .

WORKDIR "/src"
RUN dotnet build "pastapp.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "pastapp.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "pastapp.dll"]